# -*- coding: utf-8 -*-
"""Hub API client for submitting and approving skills.

This module provides a client for interacting with the enterprise
Hub API to submit skills for approval and auto-approve them.
"""
import json
import logging
from typing import Any
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class HubSubmitter:
    """Client for submitting skills to the enterprise Hub.

    Handles skill submission and optional auto-approval workflows.
    """

    def __init__(
        self,
        hub_url: str,
        timeout: int = 30,
        retries: int = 3,
    ):
        """Initialize the Hub submitter.

        Args:
            hub_url: Base URL of the Hub server.
            timeout: HTTP timeout in seconds.
            retries: Number of retry attempts.
        """
        self.hub_url = hub_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries

    def submit_skill(
        self,
        slug: str,
        name: str,
        description: str,
        content: str,
        files: dict[str, str] | None = None,
        version: str = "1.0.0",
    ) -> dict[str, Any]:
        """Submit a skill to the Hub for approval.

        Args:
            slug: Unique skill identifier.
            name: Skill display name.
            description: Skill description.
            content: SKILL.md content.
            files: Additional skill files (references/, scripts/).
            version: Skill version.

        Returns:
            Response dict with approval_id and status.

        Raises:
            RuntimeError: If submission fails.
        """
        url = f"{self.hub_url}/api/v1/skills/submit"

        payload = {
            "slug": slug,
            "name": name,
            "description": description,
            "content": content,
            "version": version,
            "files": files or {},
        }

        try:
            response = self._http_post_json(url, payload)
            logger.info("Skill '%s' submitted successfully: %s", slug, response.get("approval_id"))
            return response
        except HTTPError as e:
            status = getattr(e, "code", 0)
            if status == 409:
                raise RuntimeError(
                    f"Skill '{slug}' already exists in Hub. "
                    f"Use a different slug or update the existing skill."
                ) from e
            raise RuntimeError(f"Failed to submit skill: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to submit skill: {e}") from e

    def approve_skill(
        self,
        approval_id: str,
        comment: str = "",
        reviewer: str = "skills-sync",
    ) -> dict[str, Any]:
        """Approve a pending skill submission.

        Note: This requires the Hub to have the private key configured
        for signature generation. The sync script can generate signatures
        client-side if auto-approve is enabled.

        Args:
            approval_id: Approval request ID.
            comment: Optional approval comment.
            reviewer: Reviewer identifier.

        Returns:
            Response dict with approval status.

        Raises:
            RuntimeError: If approval fails.
        """
        url = f"{self.hub_url}/api/v1/approvals/{approval_id}/approve"

        payload = {
            "comment": comment,
            "reviewer": reviewer,
        }

        try:
            response = self._http_post_json(url, payload)
            logger.info("Approval %s completed successfully", approval_id)
            return response
        except HTTPError as e:
            status = getattr(e, "code", 0)
            if status == 404:
                raise RuntimeError(f"Approval {approval_id} not found") from e
            if status == 400:
                raise RuntimeError(
                    f"Approval {approval_id} is not in pending status"
                ) from e
            raise RuntimeError(f"Failed to approve skill: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to approve skill: {e}") from e

    def submit_with_signature(
        self,
        slug: str,
        name: str,
        description: str,
        content: str,
        files: dict[str, str] | None = None,
        version: str = "1.0.0",
        signature: str = "",
    ) -> dict[str, Any]:
        """Submit a skill that already has a signature (direct approval).

        This bypasses the approval workflow by submitting a pre-signed skill.
        Note: This requires the Hub to support direct signature submission.

        Args:
            slug: Unique skill identifier.
            name: Skill display name.
            description: Skill description.
            content: SKILL.md content.
            files: Additional skill files.
            version: Skill version.
            signature: Pre-generated signature.

        Returns:
            Response dict with skill status.

        Raises:
            RuntimeError: If submission fails.
        """
        # Try the direct approval endpoint first
        url = f"{self.hub_url}/api/v1/skills/approve"

        payload = {
            "slug": slug,
            "name": name,
            "description": description,
            "content": content,
            "version": version,
            "files": files or {},
            "signature": signature,
        }

        try:
            response = self._http_post_json(url, payload)
            logger.info("Skill '%s' approved with pre-signed signature", slug)
            return response
        except HTTPError as e:
            if getattr(e, "code", 0) == 404:
                # Fallback: submit for approval, then approve with signature
                logger.info("Direct approve endpoint not available, using approval workflow")
                submit_result = self.submit_skill(
                    slug=slug,
                    name=name,
                    description=description,
                    content=content,
                    files=files,
                    version=version,
                )
                # Note: The standard approval endpoint generates its own signature
                # If we want to use our pre-generated signature, we need a different approach
                return submit_result
            raise RuntimeError(f"Failed to submit signed skill: {e}") from e

    def get_pending_approvals(self) -> list[dict[str, Any]]:
        """Get list of pending approval requests.

        Returns:
            List of pending approval dicts.

        Raises:
            RuntimeError: If request fails.
        """
        url = f"{self.hub_url}/api/v1/approvals/pending"

        try:
            return self._http_get_json(url)
        except Exception as e:
            raise RuntimeError(f"Failed to get pending approvals: {e}") from e

    def get_approval(self, approval_id: str) -> dict[str, Any]:
        """Get details of an approval request.

        Args:
            approval_id: Approval request ID.

        Returns:
            Approval details dict.

        Raises:
            RuntimeError: If request fails.
        """
        url = f"{self.hub_url}/api/v1/approvals/{approval_id}"

        try:
            return self._http_get_json(url)
        except HTTPError as e:
            if getattr(e, "code", 0) == 404:
                raise RuntimeError(f"Approval {approval_id} not found") from e
            raise RuntimeError(f"Failed to get approval: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to get approval: {e}") from e

    def _http_get_json(self, url: str, params: dict | None = None) -> Any:
        """Make HTTP GET request and parse JSON response."""
        full_url = url
        if params:
            full_url = f"{url}?{urlencode(params)}"

        req = Request(
            full_url,
            headers={
                "Accept": "application/json",
                "User-Agent": "copaw-skills-sync/1.0",
            },
        )

        for attempt in range(self.retries + 1):
            try:
                with urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read().decode("utf-8")
                    return json.loads(body)
            except HTTPError as e:
                if attempt < self.retries and self._is_retryable(e):
                    logger.warning("HTTP %s on %s (retry %d)", e.code, url, attempt + 1)
                    continue
                raise
            except (URLError, Exception) as e:
                if attempt < self.retries:
                    logger.warning("Error on %s (retry %d): %s", url, attempt + 1, e)
                    continue
                raise

        raise RuntimeError(f"Failed to fetch {url} after {self.retries} retries")

    def _http_post_json(
        self,
        url: str,
        data: dict,
    ) -> Any:
        """Make HTTP POST request with JSON data."""
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")

        req = Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "copaw-skills-sync/1.0",
            },
        )

        for attempt in range(self.retries + 1):
            try:
                with urlopen(req, timeout=self.timeout) as resp:
                    response_body = resp.read().decode("utf-8")
                    if response_body:
                        return json.loads(response_body)
                    return {}
            except HTTPError as e:
                if attempt < self.retries and self._is_retryable(e):
                    logger.warning("HTTP %s on %s (retry %d)", e.code, url, attempt + 1)
                    continue
                raise
            except (URLError, Exception) as e:
                if attempt < self.retries:
                    logger.warning("Error on %s (retry %d): %s", url, attempt + 1, e)
                    continue
                raise

        raise RuntimeError(f"Failed to POST {url} after {self.retries} retries")

    def _is_retryable(self, error: HTTPError) -> bool:
        """Check if an HTTP error is retryable."""
        status = getattr(error, "code", 0)
        return status in {408, 409, 425, 429, 500, 502, 503, 504}


class DirectHubApprover:
    """Client for directly approving skills with client-side signatures.

    This uses the storage layer directly to approve skills with
    pre-generated signatures, bypassing the HTTP API.
    """

    def __init__(self, data_dir: str | None = None):
        """Initialize the direct approver.

        Args:
            data_dir: Path to Hub data directory.
        """
        import sys
        from pathlib import Path

        # Add hub_enterprise to path
        hub_path = Path(__file__).parent.parent
        if str(hub_path) not in sys.path:
            sys.path.insert(0, str(hub_path))

        from hub_enterprise.storage.skills import SkillStorage

        self.storage = SkillStorage(data_dir=data_dir)

    def approve_skill_direct(
        self,
        slug: str,
        name: str,
        description: str,
        content: str,
        files: dict[str, str] | None = None,
        version: str = "1.0.0",
        signature: str = "",
        approver: str = "skills-sync",
    ) -> bool:
        """Directly approve a skill with a signature.

        This bypasses the approval workflow by directly storing
        the skill as approved with the provided signature.

        Args:
            slug: Unique skill identifier.
            name: Skill display name.
            description: Skill description.
            content: SKILL.md content.
            files: Additional skill files.
            version: Skill version.
            signature: Pre-generated signature.
            approver: Approver identifier.

        Returns:
            True if successful.

        Raises:
            RuntimeError: If approval fails.
        """
        from hub_enterprise.models import SkillBundle

        # First create as pending
        bundle = SkillBundle(
            name=name,
            content=content,
            files=files or {},
            version=version,
        )

        self.storage.create_pending(
            slug=slug,
            name=name,
            description=description,
            version=version,
            bundle=bundle,
        )

        # Then approve with signature
        success = self.storage.approve_skill(
            slug=slug,
            signature=signature,
            approver=approver,
        )

        if not success:
            raise RuntimeError(f"Failed to approve skill '{slug}'")

        logger.info("Skill '%s' approved directly with signature", slug)
        return True
