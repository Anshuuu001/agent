from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.schemas.tasks import DynamicPlan

class ChatMessageCreate(BaseModel):
    content: str
    role: str = "user"
    session_id: Optional[str] = None
    message_type: str = "text"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChatMessageRead(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    message_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime

    class Config:
        from_attributes = True

class ChatSessionCreate(BaseModel):
    user_id: Optional[str] = None
    active_project_id: Optional[str] = None
    autonomy_level: int = 2

class ChatSessionRead(BaseModel):
    id: str
    session_token: str
    autonomy_level: int
    is_active: bool
    created_at: datetime
    last_active_at: datetime
    messages: List[ChatMessageRead] = Field(default_factory=list)

    class Config:
        from_attributes = True

class BrainResponse(BaseModel):
    session_id: str
    reply_text: str
    intent_detected: str
    goal: Optional[str] = None
    plan: Optional[DynamicPlan] = None
    task_id: Optional[str] = None
    requires_approval: bool = False
    suggested_actions: List[str] = Field(default_factory=list)
