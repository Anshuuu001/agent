from enum import Enum

class TaskStatus(str, Enum):
    QUEUED = "QUEUED"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"

class Priority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"

class AutonomyLevel(int, Enum):
    ASSISTED = 1      # Level 1: Ask before most actions
    SUPERVISED = 2    # Level 2: Execute normal actions, ask for sensitive
    AUTONOMOUS = 3    # Level 3: Execute most independently
    FULL_WORKFLOW = 4 # Level 4: Full long-running with only critical approvals

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class PermissionLevel(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"

class ToolCategory(str, Enum):
    DESKTOP = "DESKTOP"
    FILES = "FILES"
    SYSTEM = "SYSTEM"
    BROWSER = "BROWSER"
    APPLICATION = "APPLICATION"
    VISION = "VISION"

class AgentCategory(str, Enum):
    RESEARCH = "RESEARCH"
    CONTENT = "CONTENT"
    ENGINEERING = "ENGINEERING"
    OFFICE = "OFFICE"
    SYSTEM = "SYSTEM"
    AUTOMATION = "AUTOMATION"
    SECURITY = "SECURITY"
    GENERAL = "GENERAL"

class AgentStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    ERROR = "ERROR"
    DISABLED = "DISABLED"

class AgentHealth(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"

class MemoryTier(str, Enum):
    SHORT_TERM = "SHORT_TERM"
    TASK = "TASK"
    LONG_TERM = "LONG_TERM"
    APPLICATION = "APPLICATION"
    WORKFLOW = "WORKFLOW"

class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
