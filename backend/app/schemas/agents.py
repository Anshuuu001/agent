from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.schemas.common import AgentStatus, AgentHealth, AgentCategory

class AgentCapabilitySchema(BaseModel):
    capability_name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

class AgentBase(BaseModel):
    name: str
    display_name: str
    description: str
    category: AgentCategory = AgentCategory.GENERAL
    version: str = "1.0.0"
    required_tools: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)

class AgentCreate(AgentBase):
    capabilities: List[AgentCapabilitySchema] = Field(default_factory=list)

class AgentRead(AgentBase):
    id: str
    status: AgentStatus = AgentStatus.IDLE
    health: AgentHealth = AgentHealth.HEALTHY
    is_active: bool = True
    capabilities: List[AgentCapabilitySchema] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True

class AgentExecutionRequest(BaseModel):
    agent_name: str
    task_id: Optional[str] = None
    subtask_id: Optional[str] = None
    instruction: str
    context: Dict[str, Any] = Field(default_factory=dict)

class AgentExecutionResult(BaseModel):
    agent_name: str
    status: str  # SUCCESS, FAILED, WAITING
    output: Dict[str, Any] = Field(default_factory=dict)
    summary: str
    tools_used: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    execution_time_ms: float = 0.0
