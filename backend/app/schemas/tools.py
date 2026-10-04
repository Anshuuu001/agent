from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.schemas.common import ToolCategory, RiskLevel, PermissionLevel

class ToolBase(BaseModel):
    name: str
    display_name: str
    description: str
    category: ToolCategory
    risk_level: RiskLevel = RiskLevel.LOW
    permission_level: PermissionLevel = PermissionLevel.READ
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)

class ToolCreate(ToolBase):
    is_active: bool = True

class ToolRead(ToolBase):
    id: str
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class ToolExecuteRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    task_id: Optional[str] = None
    subtask_id: Optional[str] = None
    agent_name: Optional[str] = None
    bypass_approval_if_allowed: bool = False

class ToolExecuteResponse(BaseModel):
    tool_name: str
    status: str  # SUCCESS, FAILED, REQUIRES_APPROVAL, BLOCKED
    result: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    risk_level: RiskLevel
    audit_id: Optional[str] = None
    requires_approval: bool = False
    approval_id: Optional[str] = None
