# -*- coding: utf-8 -*-
"""Skills management API (compatible with CoPaw skills_hub.py)."""
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from ..storage.skills import SkillStorage


class SubmitSkillRequest(BaseModel):
    """Request model for submitting a skill."""

    slug: str
    name: str
    description: str
    content: str
    version: str = "1.0.0"
    files: Dict[str, str] = {}


router = APIRouter(prefix="/api/v1", tags=["skills"])
storage = SkillStorage()


@router.get("/search")
async def search_skills(
    request: Request,
    q: str = Query(""),
    limit: int = Query(20),
) -> Dict[str, Any]:
    """Search approved skills (compatible with CoPaw search_hub_skills).

    CoPaw calls: search_hub_skills(query, limit)
    Environment: COPAW_SKILLS_HUB_BASE_URL + COPAW_SKILLS_HUB_SEARCH_PATH
    """
    results = storage.search(query=q, status="approved", limit=limit)

    # Compatible with CoPaw's _norm_search_items format
    base_url = str(request.base_url)
    return {
        "items": [
            {
                "slug": s.slug,
                "name": s.name,
                "displayName": s.name,
                "description": s.description,
                "summary": s.description,
                "version": s.version,
                "url": f"{base_url}api/v1/skills/{s.slug}",
            }
            for s in results
        ]
    }


@router.get("/skills/{slug}")
async def get_skill(slug: str) -> Dict[str, Any]:
    """Get skill details (compatible with CoPaw _fetch_bundle_from_clawhub_slug).

    CoPaw calls: install_skill_from_hub(bundle_url)
    Environment: COPAW_SKILLS_HUB_BASE_URL + COPAW_SKILLS_HUB_DETAIL_PATH
    """
    skill = storage.get_by_slug(slug)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    if skill.status != "approved":
        raise HTTPException(status_code=403, detail="Skill not approved")

    bundle = storage.get_bundle(skill)

    # Include SKILL.md in files dict for CoPaw compatibility
    # CoPaw's skills_hub.py expects SKILL.md in files (line 690-691)
    files_with_skill_md = dict(bundle.files)
    if bundle.content and "SKILL.md" not in files_with_skill_md:
        files_with_skill_md["SKILL.md"] = bundle.content

    # Compatible with CoPaw's _normalize_bundle format
    # CoPaw expects content and files inside skill object (line 654-692)
    return {
        "skill": {
            "slug": skill.slug,
            "name": skill.name,
            "displayName": skill.name,
            "description": skill.description,
            "version": skill.version,
            "content": bundle.content,  # Content in skill object for CoPaw
            "files": files_with_skill_md,  # Files in skill object for CoPaw
        },
        "version": {
            "version": skill.version,
            "files": [
                {"path": path, "size": len(content)}
                for path, content in files_with_skill_md.items()
            ],
        },
        "name": skill.name,
        "content": bundle.content,  # Also at top level for compatibility
        "files": files_with_skill_md,  # Also at top level for compatibility
        "signature": skill.signature,
    }


@router.get("/skills/{slug}/file")
async def get_skill_file(
    slug: str,
    path: str = Query(...),
) -> str:
    """Get skill file (compatible with CoPaw _hub_file_path)."""
    skill = storage.get_by_slug(slug)
    if not skill or skill.status != "approved":
        raise HTTPException(status_code=404, detail="Skill not found")

    bundle = storage.get_bundle(skill)
    if path not in bundle.files:
        raise HTTPException(status_code=404, detail="File not found")

    return bundle.files[path]


@router.post("/skills/submit")
async def submit_skill(request: SubmitSkillRequest) -> Dict[str, Any]:
    """Submit a new skill for approval (internal API)."""
    # Check if slug already exists
    existing = storage.get_by_slug(request.slug)
    if existing and existing.status == "approved":
        raise HTTPException(status_code=409, detail="Skill already exists")

    from ..models import SkillBundle
    from ..storage.approvals import ApprovalStorage

    bundle = SkillBundle(
        name=request.name,
        content=request.content,
        files=request.files,
        version=request.version,
    )

    # Create pending skill
    storage.create_pending(
        request.slug,
        request.name,
        request.description,
        request.version,
        bundle,
    )

    # Create approval request
    approval_storage = ApprovalStorage()
    approval_id = approval_storage.create(request.slug, bundle)

    return {
        "slug": request.slug,
        "status": "pending",
        "approval_id": approval_id,
    }
