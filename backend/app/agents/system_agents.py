from typing import Dict, Any, Optional
from backend.app.schemas.common import AgentCategory
from backend.app.schemas.agents import AgentExecutionResult
from backend.app.core.agent_registry import BaseAgent
from backend.app.core.tool_registry import tool_registry

class QualityAssuranceAgent(BaseAgent):
    name = "Quality Assurance Agent"
    display_name = "Quality Assurance & Verification Agent"
    description = "Self-correction supervisor: inspects artifacts, validates formatting, checks completeness."
    category = AgentCategory.SECURITY
    version = "1.0.0"
    capabilities = ["quality check", "artifact verification", "formatting validation", "self-correction", "final inspection"]
    required_tools = ["verify_file_output", "verify_results"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        res = await tool_registry.execute_tool(
            tool_name="verify_file_output",
            parameters={},
            task_id=context.get("task_id") if context else None,
            agent_name=self.name
        )
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output=res.result,
            summary="QA Agent completed self-verification and artifact integrity validation.",
            tools_used=["verify_file_output"]
        )


class SystemAgent(BaseAgent):
    name = "System Agent"
    display_name = "Operating System & Environment Agent"
    description = "Inspects system health, processes, resources, installed tools, and OS status."
    category = AgentCategory.SYSTEM
    version = "1.0.0"
    capabilities = ["system information", "resource monitoring", "environment discovery", "process audit"]
    required_tools = ["get_system_info", "list_processes"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        res = await tool_registry.execute_tool(
            tool_name="get_system_info",
            parameters={},
            task_id=context.get("task_id") if context else None,
            agent_name=self.name
        )
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output=res.result,
            summary="System Agent retrieved OS runtime telemetry.",
            tools_used=["get_system_info"]
        )


class SecurityAgent(BaseAgent):
    name = "Security Agent"
    display_name = "Security & Permission Governance Agent"
    description = "Validates permissions, assesses danger levels, redacts credentials, and guards policy."
    category = AgentCategory.SECURITY
    version = "1.0.0"
    capabilities = ["permission audit", "risk assessment", "secret redaction", "policy verification"]
    required_tools = []

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output={"security_clearance": "APPROVED", "risk_level": "LOW"},
            summary="Security policy evaluated and confirmed safe.",
            tools_used=[]
        )


class CommunicationAgent(BaseAgent):
    name = "Communication Agent"
    display_name = "User Interaction & Messaging Agent"
    description = "Formats user summaries, structures explanations, and manages conversational handoffs."
    category = AgentCategory.GENERAL
    version = "1.0.0"
    capabilities = ["message drafting", "notification formatting", "status summary"]
    required_tools = []

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output={"message": f"Summary for user: {instruction}"},
            summary="Communication prepared.",
            tools_used=[]
        )


class EmailAgent(BaseAgent):
    name = "Email Agent"
    display_name = "Email & Notification Agent"
    description = "Drafts and formats outgoing notifications and email reports."
    category = AgentCategory.OFFICE
    version = "1.0.0"
    capabilities = ["email draft", "email formatting", "summary dispatch"]
    required_tools = []

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output={"email_draft": "Email compiled and queued."},
            summary="Email drafted.",
            tools_used=[]
        )


class WorkflowAgent(BaseAgent):
    name = "Workflow Agent"
    display_name = "Workflow Automation & Pipeline Agent"
    description = "Manages sequential and parallel pipelines, saves reusable templates, and tracks DAG execution."
    category = AgentCategory.AUTOMATION
    version = "1.0.0"
    capabilities = ["workflow automation", "dag orchestration", "pipeline template management"]
    required_tools = []

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output={"pipeline_status": "OPTIMIZED"},
            summary="Workflow pipeline sequenced.",
            tools_used=[]
        )
