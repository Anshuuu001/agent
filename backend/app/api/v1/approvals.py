import json
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.db.database import get_db
from backend.app.db.models import Approval as ApprovalModel
from backend.app.core.events import event_bus

router = APIRouter(prefix="/approvals", tags=["Approvals"])

class ApprovalResolveRequest(BaseModel):
    action: str  # APPROVE or REJECT
    resolved_by: str = "user"

@router.get("")
async def list_approvals(status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    stmt = select(ApprovalModel)
    if status:
        stmt = stmt.where(ApprovalModel.status == status)
    stmt = stmt.order_by(desc(ApprovalModel.requested_at)).limit(50)
    res = await db.execute(stmt)
    approvals = res.scalars().all()
    return [
        {
            "id": a.id,
            "task_id": a.task_id,
            "subtask_id": a.subtask_id,
            "tool_name": a.tool_name,
            "action_type": a.action_type,
            "risk_level": a.risk_level,
            "reason": a.reason,
            "status": a.status,
            "details": json.loads(a.details_json or "{}"),
            "requested_at": a.requested_at.isoformat() if a.requested_at else None,
            "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
            "resolved_by": a.resolved_by
        } for a in approvals
    ]

@router.post("/{approval_id}/resolve")
async def resolve_approval(approval_id: str, payload: ApprovalResolveRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(ApprovalModel).where(ApprovalModel.id == approval_id)
    res = await db.execute(stmt)
    approval = res.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    approval.status = "APPROVED" if payload.action.upper() == "APPROVE" else "REJECTED"
    approval.resolved_at = datetime.now(timezone.utc)
    approval.resolved_by = payload.resolved_by
    await db.commit()

    await event_bus.broadcast("approval_resolved", {
        "approval_id": approval.id,
        "status": approval.status,
        "resolved_by": approval.resolved_by
    })

    return {"id": approval.id, "status": approval.status}
