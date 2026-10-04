import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.db.database import get_db
from backend.app.db.models import AuditLog as AuditLogModel

router = APIRouter(prefix="/audit", tags=["Audit"])

@router.get("")
async def list_audit_logs(
    task_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AuditLogModel)
    if task_id:
        stmt = stmt.where(AuditLogModel.task_id == task_id)
    if tool_name:
        stmt = stmt.where(AuditLogModel.tool_name == tool_name)

    stmt = stmt.order_by(desc(AuditLogModel.timestamp)).limit(limit)
    res = await db.execute(stmt)
    entries = res.scalars().all()

    return [
        {
            "id": e.id,
            "task_id": e.task_id,
            "agent_name": e.agent_name,
            "tool_name": e.tool_name,
            "action": e.action,
            "parameters": json.loads(e.parameters_safe_json or "{}"),
            "result_summary": e.result_summary,
            "risk_level": e.risk_level,
            "approval_status": e.approval_status,
            "user_ip": e.user_ip,
            "is_redacted": e.is_redacted,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None
        } for e in entries
    ]
