# -*- coding: utf-8 -*-
"""Audit log API."""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..storage.audit import AuditStorage


router = APIRouter(prefix="/api/v1", tags=["audit"])
audit_storage = AuditStorage()


@router.post("/audit/logs")
async def create_audit_log(
    employee_id: str,
    action: str,
    resource_type: str,
    resource_name: str,
    details: Dict[str, Any] | None = None,
    status: str = "success",
) -> Dict[str, Any]:
    """Create audit log (CoPaw client calls this).

    Args:
        employee_id: Employee ID (from environment variable).
        action: Action type (install_skill/enable_skill/disable_skill/search_skill).
        resource_type: Resource type (skill).
        resource_name: Resource name (skill name).
        details: Additional details.
        status: Action status (success/failed).
    """
    log_id = audit_storage.create_log(
        employee_id=employee_id,
        action=action,
        resource_type=resource_type,
        resource_name=resource_name,
        details=details or {},
        status=status,
        timestamp=datetime.utcnow(),
    )

    return {
        "log_id": log_id,
        "status": "logged",
    }


@router.get("/audit/logs")
async def list_audit_logs(
    employee_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_name: Optional[str] = Query(None),
    limit: int = Query(100),
) -> List[Dict[str, Any]]:
    """Query audit logs (admin API)."""
    logs = audit_storage.list_logs(
        employee_id=employee_id,
        action=action,
        resource_name=resource_name,
        limit=limit,
    )

    return [
        {
            "log_id": log.id,
            "employee_id": log.employee_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_name": log.resource_name,
            "details": log.details,
            "status": log.status,
            "timestamp": log.timestamp.isoformat(),
        }
        for log in logs
    ]


@router.get("/audit/logs/{log_id}")
async def get_audit_log(log_id: str) -> Dict[str, Any]:
    """Get single audit log details."""
    log = audit_storage.get_log(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")

    return {
        "log_id": log.id,
        "employee_id": log.employee_id,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_name": log.resource_name,
        "details": log.details,
        "status": log.status,
        "timestamp": log.timestamp.isoformat(),
    }
