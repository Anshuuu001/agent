import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
from backend.app.db.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=True)
    full_name = Column(String(128), nullable=True)
    role = Column(String(32), default="owner")
    preferences_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(32), default="ACTIVE", index=True)  # ACTIVE, ARCHIVED, COMPLETED
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    goal = Column(Text, nullable=False)
    priority = Column(String(16), default="NORMAL", index=True)  # LOW, NORMAL, HIGH, URGENT
    status = Column(String(32), default="QUEUED", index=True)   # QUEUED, PLANNING, RUNNING, WAITING, PAUSED, COMPLETED, FAILED, CANCELLED, REQUIRES_APPROVAL
    progress = Column(Float, default=0.0)
    assigned_agents_json = Column(Text, default="[]")
    result_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    requires_approval = Column(Boolean, default=False)
    plan_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utc_now, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    project = relationship("Project", back_populates="tasks")
    subtasks = relationship("Subtask", back_populates="task", cascade="all, delete-orphan", order_by="Subtask.step_order")
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="task", cascade="all, delete-orphan")
    checkpoints = relationship("Checkpoint", back_populates="task", cascade="all, delete-orphan")
    file_records = relationship("FileRecord", back_populates="task", cascade="all, delete-orphan")


class Subtask(Base):
    __tablename__ = "subtasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    agent_name = Column(String(64), nullable=True)
    tool_name = Column(String(64), nullable=True)
    status = Column(String(32), default="QUEUED", index=True)  # QUEUED, RUNNING, COMPLETED, FAILED, SKIPPED, PAUSED
    step_order = Column(Integer, default=0)
    input_data_json = Column(Text, default="{}")
    output_data_json = Column(Text, default="{}")
    error = Column(Text, nullable=True)
    requires_approval = Column(Boolean, default=False)
    is_parallel_safe = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    task = relationship("Task", back_populates="subtasks")


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    predecessor_subtask_id = Column(String(36), nullable=False)
    successor_subtask_id = Column(String(36), nullable=False)
    dependency_type = Column(String(32), default="FINISH_TO_START")
    created_at = Column(DateTime, default=utc_now)


class TaskLog(Base):
    __tablename__ = "task_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    subtask_id = Column(String(36), nullable=True)
    level = Column(String(16), default="INFO")  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    agent_name = Column(String(64), nullable=True)
    message = Column(Text, nullable=False)
    details_json = Column(Text, default="{}")
    timestamp = Column(DateTime, default=utc_now, index=True)

    task = relationship("Task", back_populates="logs")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(64), unique=True, nullable=False, index=True)
    display_name = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(64), default="GENERAL")
    version = Column(String(32), default="1.0.0")
    status = Column(String(32), default="IDLE")  # IDLE, RUNNING, WAITING, ERROR, DISABLED
    health = Column(String(32), default="HEALTHY")  # HEALTHY, DEGRADED, UNHEALTHY
    required_tools_json = Column(Text, default="[]")
    permissions_json = Column(Text, default="[]")
    input_schema_json = Column(Text, default="{}")
    output_schema_json = Column(Text, default="{}")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    capabilities = relationship("AgentCapability", back_populates="agent", cascade="all, delete-orphan")


class AgentCapability(Base):
    __tablename__ = "agent_capabilities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    capability_name = Column(String(128), nullable=False, index=True)
    description = Column(Text, nullable=True)
    parameters_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utc_now)

    agent = relationship("Agent", back_populates="capabilities")


class Tool(Base):
    __tablename__ = "tools"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(64), unique=True, nullable=False, index=True)
    display_name = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(64), nullable=False, index=True)  # DESKTOP, FILES, SYSTEM, BROWSER, APPLICATION, VISION
    risk_level = Column(String(16), default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    permission_level = Column(String(32), default="READ")  # READ, WRITE, EXECUTE, SYSTEM_ADMIN
    input_schema_json = Column(Text, default="{}")
    output_schema_json = Column(Text, default="{}")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)


class ToolExecution(Base):
    __tablename__ = "tool_executions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), nullable=True, index=True)
    subtask_id = Column(String(36), nullable=True)
    tool_name = Column(String(64), nullable=False, index=True)
    agent_name = Column(String(64), nullable=True)
    input_parameters_json = Column(Text, default="{}")
    output_result_json = Column(Text, default="{}")
    status = Column(String(32), default="SUCCESS")  # SUCCESS, FAILED, BLOCKED, TIMEOUT
    execution_time_ms = Column(Float, default=0.0)
    risk_level = Column(String(16), default="LOW")
    approved_by = Column(String(64), nullable=True)
    error = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utc_now, index=True)


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    subtask_id = Column(String(36), nullable=True)
    tool_name = Column(String(64), nullable=True)
    action_type = Column(String(64), default="TOOL_EXECUTION")
    risk_level = Column(String(16), default="MEDIUM")
    reason = Column(Text, nullable=False)
    status = Column(String(32), default="PENDING", index=True)  # PENDING, APPROVED, REJECTED, EXPIRED
    details_json = Column(Text, default="{}")
    requested_at = Column(DateTime, default=utc_now)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(64), nullable=True)

    task = relationship("Task", back_populates="approvals")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scope = Column(String(64), nullable=False)  # GLOBAL, FILE, APP, NETWORK, SHELL
    autonomy_level = Column(Integer, default=2)  # 1, 2, 3, 4
    action_name = Column(String(128), nullable=False)
    is_allowed = Column(Boolean, default=True)
    requires_confirmation = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)


class Memory(Base):
    __tablename__ = "memories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tier = Column(String(32), nullable=False, index=True)  # SHORT_TERM, TASK, LONG_TERM, APPLICATION, WORKFLOW
    key = Column(String(128), nullable=False, index=True)
    content = Column(Text, nullable=False)
    context_type = Column(String(64), default="GENERAL")
    task_id = Column(String(36), nullable=True, index=True)
    metadata_json = Column(Text, default="{}")
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime, default=utc_now)
    created_at = Column(DateTime, default=utc_now)


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(128), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    tags_json = Column(Text, default="[]")
    is_reusable = Column(Boolean, default=True)
    created_by = Column(String(64), default="system")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowStep.step_order")


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    step_order = Column(Integer, default=0)
    title = Column(String(128), nullable=False)
    agent_name = Column(String(64), nullable=True)
    tool_name = Column(String(64), nullable=True)
    parameters_template_json = Column(Text, default="{}")
    depends_on_step = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    workflow = relationship("Workflow", back_populates="steps")


class FileRecord(Base):
    __tablename__ = "file_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    file_path = Column(Text, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, default=0)
    mime_type = Column(String(128), default="application/octet-stream")
    file_category = Column(String(64), default="OUTPUT")  # INPUT, OUTPUT, INTERMEDIATE, BACKUP
    action_performed = Column(String(64), default="CREATED")  # CREATED, MODIFIED, READ, DELETED
    hash_checksum = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    task = relationship("Task", back_populates="file_records")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_token = Column(String(128), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    active_project_id = Column(String(36), nullable=True)
    autonomy_level = Column(Integer, default=2)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    last_active_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.timestamp")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(16), nullable=False)  # user, assistant, system, agent, tool
    content = Column(Text, nullable=False)
    message_type = Column(String(32), default="text")  # text, plan, task_update, approval_request, error
    metadata_json = Column(Text, default="{}")
    timestamp = Column(DateTime, default=utc_now, index=True)

    session = relationship("Session", back_populates="messages")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(32), default="INFO")  # INFO, SUCCESS, WARNING, ERROR, APPROVAL
    priority = Column(String(16), default="NORMAL")  # LOW, NORMAL, HIGH, URGENT
    is_read = Column(Boolean, default=False, index=True)
    action_url = Column(String(255), nullable=True)
    task_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    state_snapshot_json = Column(Text, nullable=False)
    file_backups_json = Column(Text, default="[]")
    can_rollback = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    task = relationship("Task", back_populates="checkpoints")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), nullable=True, index=True)
    agent_name = Column(String(64), nullable=True)
    tool_name = Column(String(64), nullable=True)
    action = Column(String(128), nullable=False, index=True)
    parameters_safe_json = Column(Text, default="{}")
    result_summary = Column(Text, nullable=True)
    risk_level = Column(String(16), default="LOW")
    approval_status = Column(String(32), default="AUTO_APPROVED")
    user_ip = Column(String(45), default="127.0.0.1")
    is_redacted = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=utc_now, index=True)


class ModelConfiguration(Base):
    __tablename__ = "model_configurations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_name = Column(String(128), unique=True, nullable=False)
    provider = Column(String(64), nullable=False)  # openai, anthropic, ollama, heuristic, local
    model_type = Column(String(32), default="REASONING")  # FAST, REASONING, VISION, CODING, SPEECH
    context_window = Column(Integer, default=128000)
    cost_tier = Column(String(16), default="STANDARD")
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    config_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utc_now)


class Plugin(Base):
    __tablename__ = "plugins"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(128), unique=True, nullable=False)
    display_name = Column(String(128), nullable=False)
    version = Column(String(32), default="1.0.0")
    author = Column(String(128), default="Community")
    description = Column(Text, nullable=True)
    capabilities_json = Column(Text, default="[]")
    required_permissions_json = Column(Text, default="[]")
    is_enabled = Column(Boolean, default=False)
    config_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utc_now)
