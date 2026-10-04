from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.schemas.common import MemoryTier

class MemoryBase(BaseModel):
    tier: MemoryTier
    key: str
    content: str
    context_type: str = "GENERAL"
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MemoryCreate(MemoryBase):
    pass

class MemoryRead(MemoryBase):
    id: str
    access_count: int = 0
    last_accessed_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class MemoryQuery(BaseModel):
    query: str
    tier: Optional[MemoryTier] = None
    context_type: Optional[str] = None
    task_id: Optional[str] = None
    limit: int = 20
