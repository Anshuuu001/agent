from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class WorkflowStepSchema(BaseModel):
    step_order: int
    title: str
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    parameters_template: Dict[str, Any] = Field(default_factory=dict)
    depends_on_step: Optional[int] = None

class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_reusable: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WorkflowCreate(WorkflowBase):
    steps: List[WorkflowStepSchema] = Field(default_factory=list)

class WorkflowRead(WorkflowBase):
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    steps: List[WorkflowStepSchema] = Field(default_factory=list)

    class Config:
        from_attributes = True
