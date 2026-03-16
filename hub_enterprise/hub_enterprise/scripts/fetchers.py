# -*- coding: utf-8 -*-
"""Skill fetchers for various sources.

This module provides fetcher classes for retrieving skill bundles
from GitHub, skills.sh, and skillsmp.com, reusing the logic from
src/copaw/agents/skills_hub.py.
"""
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote, urlparse
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import os
import base64
import time

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    """Result of a skill fetch operation.

    Attributes:
        name: Skill name.
        content: SKILL.md content.
        files: Dictionary of additional files.
        version: Skill version.
        source_url: Original source URL.
        slug: Normalized skill slug.
    """

    name: str
    content: str
    files: dict[str, str]
    version: str = "1.0.0"
    source_url: str = ""
    slug: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API submission."""
        return {
            "name": self.name,
            "content": self.content,
            "files": self.files,
            "version": self.version,
        }


# HTTP utility functions (reused from skills_hub.py)

RETRYABLE_HTTP_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


def _compute_backoff_seconds(attempt: int) -> float:
    """Compute exponential backoff delay."""
    base = 0.8
    cap = 6.0
    return min(cap, base * (2 ** max(0, attempt - 1)))


def _http_get(
    url: str,
    accept: str = "application/json",
) -> str:
    """Make HTTP GET request with retries.

    Args:
        url: URL to fetch.
        accept: Accept header value.

    Returns:
        Response body as string.
    """
    retries = 3
    timeout = 15.0
    attempts = retries + 1
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        req = Request(
            url,
            headers={
                "Accept": accept,
                "User-Agent": "copaw-skills-sync/1.0",
            },
        )
        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
        github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if github_token and "api.github.com" in host:
            req.add_header("Authorization", f"Bearer {github_token}")

        try:
            with urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except HTTPError as e:
            last_error = e
            status = getattr(e, "code", 0) or 0
            if status == 403 and "api.github.com" in host:
                raise RuntimeError(
                    "GitHub API rate limit exceeded. Set GITHUB_TOKEN to increase limit."
                ) from e
            if attempt < attempts and status in RETRYABLE_HTTP_STATUS:
                delay = _compute_backoff_seconds(attempt)
                logger.warning(
                    "HTTP %s on %s (attempt %d/%d), retrying in %.2fs",
                    status,
                    url,
                    attempt,
                    attempts,
                    delay,
                )
                time.sleep(delay)
                continue
            raise
        except Exception as e:
            last_error = e
            if attempt < attempts:
                delay = _compute_backoff_seconds(attempt)
                logger.warning("Error on %s (attempt %d/%d): %s", url, attempt, attempts, e)
                time.sleep(delay)
                continue
            raise

    if last_error is not None:
        raise last_error
    raise RuntimeError(f"Failed to fetch URL: {url}")


def _http_json_get(url: str, params: dict | None = None) -> Any:
    """Make HTTP GET request and parse JSON response.

    Args:
        url: URL to fetch.
        params: Optional query parameters.

    Returns:
        Parsed JSON response.
    """
    import json
    from urllib.parse import urlencode

    full_url = url
    if params:
        full_url = f"{url}?{urlencode(params)}"
    body = _http_get(full_url, accept="application/json")
    return json.loads(body)


def _http_text_get(url: str) -> str:
    """Make HTTP GET request for text content."""
    return _http_get(url, accept="text/plain, text/markdown, */*")


# GitHub utility functions (reused from skills_hub.py)

def _github_api_url(owner: str, repo: str, suffix: str) -> str:
    """Build GitHub API URL."""
    base = f"https://api.github.com/repos/{owner}/{repo}"
    cleaned = suffix.lstrip("/")
    return f"{base}/{cleaned}" if cleaned else base


def _github_get_default_branch(owner: str, repo: str) -> str:
    """Get default branch for a GitHub repository."""
    repo_meta = _http_json_get(_github_api_url(owner, repo, ""))
    if isinstance(repo_meta, dict):
        branch = repo_meta.get("default_branch")
        if isinstance(branch, str) and branch.strip():
            return branch.strip()
    return "main"


def _github_read_file(entry: dict[str, Any]) -> str:
    """Read file content from GitHub API entry."""
    download_url = entry.get("download_url")
    if isinstance(download_url, str) and download_url:
        return _http_text_get(download_url)

    content = entry.get("content")
    if isinstance(content, str) and content:
        try:
            normalized = content.replace("\n", "")
            return base64.b64decode(normalized).decode("utf-8", errors="replace")
        except Exception:
            pass

    raise ValueError("Unable to read file content from GitHub entry")


def _github_get_content_entry(
    owner: str,
    repo: str,
    path: str,
    ref: str,
) -> dict[str, Any]:
    """Get content entry from GitHub."""
    content_url = _github_api_url(owner, repo, f"contents/{path}")
    data = _http_json_get(content_url, {"ref": ref})
    if not isinstance(data, dict):
        raise ValueError(f"Unexpected GitHub response for path: {path}")
    return data


def _github_get_dir_entries(
    owner: str,
    repo: str,
    path: str,
    ref: str,
) -> list[dict[str, Any]]:
    """Get directory entries from GitHub."""
    content_url = _github_api_url(owner, repo, f"contents/{path}")
    data = _http_json_get(content_url, {"ref": ref})
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


def _join_repo_path(root: str, leaf: str) -> str:
    """Join repository path components."""
    if not root:
        return leaf
    return f"{root.rstrip('/')}/{leaf.lstrip('/')}"


def _relative_from_root(full_path: str, root: str) -> str:
    """Get relative path from root."""
    if not root:
        return full_path.lstrip("/")
    prefix = f"{root.rstrip('/')}/"
    if full_path.startswith(prefix):
        return full_path[len(prefix):]
    return full_path


def _github_collect_tree_files(
    owner: str,
    repo: str,
    ref: str,
    root: str,
    subdir: str,
    max_files: int = 200,
) -> dict[str, str]:
    """Collect files from a GitHub tree directory."""
    files: dict[str, str] = {}
    pending = [_join_repo_path(root, subdir)]
    visited = 0

    while pending:
        current_dir = pending.pop()
        entries = _github_get_dir_entries(owner, repo, current_dir, ref)
        for entry in entries:
            entry_type = str(entry.get("type") or "")
            entry_path = str(entry.get("path") or "")
            if not entry_path:
                continue
            if entry_type == "dir":
                pending.append(entry_path)
                continue
            if entry_type != "file":
                continue
            rel = _relative_from_root(entry_path, root)
            if not (rel.startswith("references/") or rel.startswith("scripts/")):
                continue
            files[rel] = _github_read_file(entry)
            visited += 1
            if visited >= max_files:
                logger.warning("File collection capped at %d files", max_files)
                return files
    return files


def _normalize_skill_key(text: str) -> str:
    """Normalize skill name for comparison."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# Fetcher classes

class SkillFetcher(ABC):
    """Abstract base class for skill fetchers."""

    @abstractmethod
    def fetch(self, identifier: str, version: str = "") -> FetchResult:
        """Fetch a skill bundle.

        Args:
            identifier: Source-specific identifier (URL, slug, etc.).
            version: Optional version/branch/tag.

        Returns:
            FetchResult with skill data.

        Raises:
            ValueError: If identifier is invalid.
            RuntimeError: If fetch fails.
        """
        pass


class GitHubFetcher(SkillFetcher):
    """Fetcher for GitHub repositories.

    Supports both direct GitHub URLs and owner/repo specifications.
    """

    def fetch(self, identifier: str, version: str = "") -> FetchResult:
        """Fetch skill from GitHub.

        Args:
            identifier: GitHub URL or owner/repo spec.
            version: Optional branch/tag.

        Returns:
            FetchResult with skill data.
        """
        spec = self._parse_github_url(identifier)
        if spec is None:
            raise ValueError(
                f"Invalid GitHub URL or format: {identifier}. "
                "Use: https://github.com/owner/repo or owner/repo"
            )

        owner, repo, branch_in_url, path_hint = spec
        path_hint = path_hint.strip("/")

        # Normalize path_hint if it points to SKILL.md
        if path_hint.endswith("/SKILL.md"):
            path_hint = path_hint[: -len("/SKILL.md")]
        elif path_hint == "SKILL.md":
            path_hint = ""

        branch = version.strip() or branch_in_url.strip()

        # Get default branch if not specified
        if not branch:
            try:
                branch = _github_get_default_branch(owner, repo)
            except Exception:
                branch = "main"

        return self._fetch_from_github(owner, repo, path_hint, branch)

    def _parse_github_url(self, url: str) -> tuple[str, str, str, str] | None:
        """Parse GitHub URL into components.

        Returns:
            (owner, repo, branch, path_hint) or None.
        """
        # Check if it's a URL
        if "://" in url:
            parsed = urlparse(url)
            host = (parsed.netloc or "").lower()
            if host not in {"github.com", "www.github.com"}:
                return None
            parts = [unquote(p) for p in parsed.path.split("/") if p]
            if len(parts) < 2:
                return None
            owner, repo = parts[0], parts[1]
            branch = ""
            path_hint = ""
            if len(parts) >= 4 and parts[2] in {"tree", "blob"}:
                branch = parts[3]
                if len(parts) > 4:
                    path_hint = "/".join(parts[4:])
            elif len(parts) > 2:
                path_hint = "/".join(parts[2:])
            return owner, repo, branch, path_hint

        # Check if it's owner/repo format
        parts = url.split("/")
        if len(parts) == 2:
            return parts[0], parts[1], "", ""

        return None

    def _fetch_from_github(
        self,
        owner: str,
        repo: str,
        path_hint: str,
        branch: str,
    ) -> FetchResult:
        """Fetch skill data from GitHub repository.

        Args:
            owner: Repository owner.
            repo: Repository name.
            path_hint: Path hint within repository.
            branch: Branch or tag.

        Returns:
            FetchResult with skill data.
        """
        skill_hint = path_hint
        source_url = f"https://github.com/{owner}/{repo}"

        # Try to find SKILL.md
        selected_root = ""
        skill_md_entry: dict[str, Any] | None = None

        # Common root locations
        roots = [
            _join_repo_path("skills", skill_hint) if skill_hint else "",
            skill_hint,
            "",
        ]
        roots = [r for r in roots if r or r == ""]

        for root in roots:
            skill_md_path = _join_repo_path(root, "SKILL.md")
            try:
                entry = _github_get_content_entry(owner, repo, skill_md_path, branch)
            except HTTPError as e:
                if getattr(e, "code", 0) == 404:
                    continue
                raise
            if str(entry.get("type") or "") == "file":
                selected_root = root
                skill_md_entry = entry
                break

        # Fallback: search for matching skill
        if skill_md_entry is None and skill_hint:
            skill_norm = _normalize_skill_key(skill_hint)
            try:
                tree_url = _github_api_url(owner, repo, f"git/trees/{branch}")
                data = _http_json_get(tree_url, {"recursive": "1"})
                if isinstance(data, dict):
                    tree = data.get("tree", [])
                    for item in tree:
                        if not isinstance(item, dict):
                            continue
                        path = item.get("path", "")
                        if not isinstance(path, str):
                            continue
                        if path.endswith("/SKILL.md"):
                            leaf = path[: -len("/SKILL.md")].split("/")[-1]
                            leaf_norm = _normalize_skill_key(leaf)
                            if leaf_norm == skill_norm or skill_norm in leaf_norm:
                                selected_root = path[: -len("/SKILL.md")]
                                try:
                                    entry = _github_get_content_entry(
                                        owner, repo, path, branch
                                    )
                                    if str(entry.get("type") or "") == "file":
                                        skill_md_entry = entry
                                        break
                                except HTTPError:
                                    continue
            except Exception as e:
                logger.warning("Failed to search for skill: %s", e)

        if skill_md_entry is None:
            raise ValueError(
                f"Could not find SKILL.md in {source_url}. "
                f"Tried paths: {roots}"
            )

        # Read SKILL.md
        content = _github_read_file(skill_md_entry)

        # Extract name from content or use path hint
        name = skill_hint.split("/")[-1] if skill_hint else repo
        try:
            import frontmatter
            post = frontmatter.loads(content)
            extracted_name = post.get("name")
            if isinstance(extracted_name, str) and extracted_name.strip():
                name = extracted_name.strip()
        except Exception:
            pass

        # Collect files from references/ and scripts/
        files: dict[str, str] = {}
        for subdir in ("references", "scripts"):
            try:
                files.update(
                    _github_collect_tree_files(
                        owner=owner,
                        repo=repo,
                        ref=branch,
                        root=selected_root,
                        subdir=subdir,
                    )
                )
            except HTTPError as e:
                if getattr(e, "code", 0) != 404:
                    raise

        return FetchResult(
            name=name,
            content=content,
            files=files,
            version=branch,
            source_url=source_url,
            slug=self._generate_slug(name),
        )

    def _generate_slug(self, name: str) -> str:
        """Generate a normalized slug from skill name."""
        return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


class SkillsShFetcher(SkillFetcher):
    """Fetcher for skills.sh URLs.

    Skills.sh URLs follow the format:
    https://skills.sh/owner/repo/skill
    """

    def fetch(self, identifier: str, version: str = "") -> FetchResult:
        """Fetch skill from skills.sh.

        Args:
            identifier: skills.sh URL.
            version: Optional version/branch.

        Returns:
            FetchResult with skill data.
        """
        spec = self._parse_skills_sh_url(identifier)
        if spec is None:
            raise ValueError(
                f"Invalid skills.sh URL: {identifier}. "
                "Use: https://skills.sh/owner/repo/skill"
            )

        owner, repo, skill = spec
        github_fetcher = GitHubFetcher()

        # Construct GitHub URL and delegate
        github_url = f"https://github.com/{owner}/{repo}/tree/main/skills/{skill}"
        return github_fetcher.fetch(github_url, version)

    def _parse_skills_sh_url(self, url: str) -> tuple[str, str, str] | None:
        """Parse skills.sh URL.

        Returns:
            (owner, repo, skill) or None.
        """
        if "://" not in url:
            return None

        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
        if host not in {"skills.sh", "www.skills.sh"}:
            return None

        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) < 3:
            return None

        return parts[0], parts[1], parts[2]


class SkillsMpFetcher(SkillFetcher):
    """Fetcher for skillsmp.com URLs.

    SkillsMP URLs use slugs that encode GitHub repository info.
    """

    def fetch(self, identifier: str, version: str = "") -> FetchResult:
        """Fetch skill from skillsmp.com.

        Args:
            identifier: skillsmp.com URL.
            version: Optional version/branch.

        Returns:
            FetchResult with skill data.
        """
        spec = self._parse_skillsmp_url(identifier)
        if spec is None:
            raise ValueError(
                f"Invalid skillsmp.com URL: {identifier}. "
                "Could not extract GitHub repository info."
            )

        owner, repo, skill_hint = spec
        github_fetcher = GitHubFetcher()

        # Construct GitHub URL and delegate
        path = f"skills/{skill_hint}" if skill_hint else ""
        github_url = f"https://github.com/{owner}/{repo}"
        if path:
            github_url += f"/tree/main/{path}"

        return github_fetcher.fetch(github_url, version)

    def _parse_skillsmp_url(self, url: str) -> tuple[str, str, str] | None:
        """Parse skillsmp.com URL to extract GitHub info.

        Returns:
            (owner, repo, skill_hint) or None.
        """
        if "://" not in url:
            return None

        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
        if host not in {"skillsmp.com", "www.skillsmp.com"}:
            return None

        parts = [p for p in parsed.path.split("/") if p]
        if not parts:
            return None

        # Find the skill slug
        slug = ""
        if "skills" in parts:
            idx = parts.index("skills")
            if idx + 1 < len(parts):
                slug = parts[idx + 1]
        else:
            slug = parts[0]

        if not slug:
            return None

        # Parse slug: owner-repo-skills-skill-name-skill-md
        if slug.endswith("-skill-md"):
            slug = slug[: -len("-skill-md")]

        tokens = [t for t in slug.split("-") if t]
        if len(tokens) < 3:
            return None

        owner = tokens[0]
        tail_tokens = tokens[1:]

        # Try to find valid repo by checking GitHub
        max_split = min(len(tail_tokens), 6)
        for i in range(max_split, 0, -1):
            repo = "-".join(tail_tokens[:i]).strip()
            if not repo:
                continue
            # Check if repo exists
            try:
                _http_json_get(_github_api_url(owner, repo, ""))
                remainder = tail_tokens[i:]
                skill_hint = "-".join(remainder).strip() if remainder else ""
                return owner, repo, skill_hint
            except Exception:
                continue

        # Fallback: use first token as repo
        repo = tail_tokens[0]
        skill_hint = "-".join(tail_tokens[1:]).strip()
        return owner, repo, skill_hint


def get_fetcher(source: str) -> SkillFetcher:
    """Get appropriate fetcher for source type.

    Args:
        source: Source type ("github", "skills-sh", "skills-mp", "auto").

    Returns:
        Appropriate SkillFetcher instance.

    Raises:
        ValueError: If source type is invalid.
    """
    fetchers = {
        "github": GitHubFetcher(),
        "skills-sh": SkillsShFetcher(),
        "skills-mp": SkillsMpFetcher(),
        "skills.mp": SkillsMpFetcher(),
        "skillsmp": SkillsMpFetcher(),
    }

    fetcher = fetchers.get(source.lower())
    if fetcher:
        return fetcher

    raise ValueError(
        f"Invalid source type: {source}. "
        f"Supported: {', '.join(fetchers.keys())}"
    )


def detect_source(identifier: str) -> str:
    """Auto-detect source type from identifier.

    Args:
        identifier: URL or identifier to check.

    Returns:
        Detected source type.
    """
    if "skills.sh" in identifier.lower():
        return "skills-sh"
    if "skillsmp.com" in identifier.lower():
        return "skills-mp"
    if "github.com" in identifier.lower():
        return "github"
    # Default to GitHub for owner/repo format
    if "/" in identifier and len(identifier.split("/")) == 2:
        return "github"
    return "github"  # Default
