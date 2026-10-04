from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.schemas.common import TaskStatus, Priority

class SubtaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    step_order: int = 0
    input_data: Dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False
    is_parallel_safe: bool = True

class SubtaskCreate(SubtaskBase):
    pass

class SubtaskRead(SubtaskBase):
    id: str
    task_id: str
    status: str
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    title: str
    goal: str
    priority: Priority = Priority.NORMAL
    project_id: Optional[str] = None

class TaskCreate(TaskBase):
    assigned_agents: List[str] = Field(default_factory=list)
    plan: Dict[str, Any] = Field(default_factory=dict)

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[TaskStatus] = None
    progress: Optional[float] = None
    result_summary: Optional[str] = None
    error_message: Optional[str] = None
    requires_approval: Optional[bool] = None

class TaskLogRead(BaseModel):
    id: str
    task_id: str
    subtask_id: Optional[str] = None
    level: str
    agent_name: Optional[str] = None
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime

    class Config:
        from_attributes = True

class TaskRead(TaskBase):
    id: str
    status: TaskStatus
    progress: float
    assigned_agents: List[str] = Field(default_factory=list)
    result_summary: Optional[str] = None
    error_message: Optional[str] = None
    requires_approval: bool = False
    subtasks: List[SubtaskRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PlanStepSchema(BaseModel):
    step_order: int
    title: str
    agent_name: str
    tool_name: Optional[str] = None
    description: str
    dependencies: List[int] = Field(default_factory=list)
    estimated_risk: str = "LOW"
    requires_approval: bool = False
    is_parallel_safe: bool = True
    parameters: Dict[str, Any] = Field(default_factory=dict)

class DynamicPlan(BaseModel):
    goal: str
    summary: str
    primary_intent: str
    required_capabilities: List[str]
    selected_agents: List[str]
    steps: List[PlanStepSchema]
    can_execute_in_parallel: bool = True
