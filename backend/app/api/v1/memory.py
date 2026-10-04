from typing import List, Optional
from fastapi import APIRouter, HTTPException
from backend.app.schemas.memory import MemoryCreate, MemoryRead, MemoryQuery
from backend.app.schemas.common import MemoryTier
from backend.app.core.memory import memory_manager

router = APIRouter(prefix="/memory", tags=["Memory"])

@router.get("")
async def search_memory(
    q: str = "",
    tier: Optional[MemoryTier] = None,
    task_id: Optional[str] = None,
    limit: int = 20
):
    return await memory_manager.retrieve(query=q, tier=tier, task_id=task_id, limit=limit)

@router.post("")
async def store_memory(payload: MemoryCreate):
    entry_id = await memory_manager.store(
        tier=payload.tier,
        key=payload.key,
        content=payload.content,
        context_type=payload.context_type,
        task_id=payload.task_id,
        metadata=payload.metadata
    )
    return {"id": entry_id, "status": "STORED"}
