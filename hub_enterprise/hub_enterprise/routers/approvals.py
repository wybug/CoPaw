# -*- coding: utf-8 -*-
"""Approval workflow API."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from ..storage.approvals import ApprovalStorage
from ..storage.skills import SkillStorage
from ..signature import SignatureGenerator
from ..config import get_private_key


router = APIRouter(prefix="/api/v1", tags=["approvals"])
approval_storage = ApprovalStorage()
skill_storage = SkillStorage()


@router.get("/approvals/pending")
async def list_pending_approvals() -> List[Dict[str, Any]]:
    """List pending approval requests."""
    approvals = approval_storage.list_pending()
    return [
        {
            "approval_id": a.id,
            "skill_slug": a.skill_slug,
            "submitted_at": a.submitted_at.isoformat(),
        }
        for a in approvals
    ]


@router.get("/approvals/{approval_id}")
async def get_approval(approval_id: str) -> Dict[str, Any]:
    """Get approval request details."""
    approval = approval_storage.get(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    skill_data = approval_storage.get_skill_data(approval_id)

    return {
        "approval_id": approval.id,
        "skill_slug": approval.skill_slug,
        "submitted_at": approval.submitted_at.isoformat(),
        "status": approval.status,
        "reviewer": approval.reviewer,
        "reviewed_at": approval.reviewed_at.isoformat() if approval.reviewed_at else None,
        "comment": approval.comment,
        "skill_data": skill_data,
    }


@router.post("/approvals/{approval_id}/approve")
async def approve_skill(
    approval_id: str,
    comment: str = "",
    reviewer: str = "",
) -> Dict[str, Any]:
    """Approve a skill (generates signature)."""
    approval = approval_storage.get(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Approval not in pending status")

    # Get skill bundle
    skill_data = approval_storage.get_skill_data(approval_id)

    # Generate signature
    private_key = get_private_key()
    if not private_key:
        raise HTTPException(status_code=500, detail="Private key not configured")

    signer = SignatureGenerator(private_key)
    signature = signer.sign_skill_bundle(skill_data)

    # Approve and store signature
    skill_storage.approve_skill(
        approval.skill_slug,
        signature=signature,
        approver=reviewer,
    )

    # Update approval status
    approval_storage.update_status(
        approval_id,
        "approved",
        reviewer=reviewer,
        comment=comment,
    )

    return {
        "approval_id": approval_id,
        "status": "approved",
        "skill": approval.skill_slug,
    }


@router.post("/approvals/{approval_id}/reject")
async def reject_skill(
    approval_id: str,
    reason: str,
    reviewer: str = "",
) -> Dict[str, Any]:
    """Reject a skill submission."""
    approval = approval_storage.get(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    approval_storage.update_status(
        approval_id,
        "rejected",
        reviewer=reviewer,
        comment=reason,
    )

    skill_storage.reject_skill(approval.skill_slug, reason=reason)

    return {
        "approval_id": approval_id,
        "status": "rejected",
        "reason": reason,
    }
