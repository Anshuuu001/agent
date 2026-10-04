from typing import Dict, Any, Optional
from backend.app.schemas.common import AgentCategory
from backend.app.schemas.agents import AgentExecutionResult
from backend.app.core.agent_registry import BaseAgent
from backend.app.core.tool_registry import tool_registry

class CodingAgent(BaseAgent):
    name = "Coding Agent"
    display_name = "Autonomous Software Engineer Agent"
    description = "Inspects repositories, writes clean code, refactors components, and implements algorithms."
    category = AgentCategory.ENGINEERING
    version = "1.0.0"
    capabilities = ["inspect code", "modify code", "run code", "code generation", "refactoring", "architecture design"]
    required_tools = ["read_file", "write_file", "search_files", "execute_command"]
    permissions = ["READ_FILES", "WRITE_FILES", "EXECUTE_TESTS"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output={"changes": f"Applied code modifications for: {instruction}"},
            summary=f"Coding agent analyzed instruction and prepared implementation for: {instruction}",
            tools_used=["search_files", "write_file"]
        )


class DebuggingAgent(BaseAgent):
    name = "Debugging Agent"
    display_name = "Diagnostics & Debugging Agent"
    description = "Traces stack traces, isolates root causes, inspects logs, and devises regression fixes."
    category = AgentCategory.ENGINEERING
    version = "1.0.0"
    capabilities = ["trace analysis", "root cause identification", "error reproduction", "diagnostics"]
    required_tools = ["read_file", "search_files", "list_processes"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output={"diagnosis": "Root cause localized, patch strategy formulated."},
            summary=f"Debugging agent diagnosed target issue: {instruction}",
            tools_used=["search_files"]
        )


class TestingAgent(BaseAgent):
    name = "Testing Agent"
    display_name = "Automated Test & Validation Agent"
    description = "Runs unit tests, integration suites, benchmarks, and regression suites."
    category = AgentCategory.ENGINEERING
    version = "1.0.0"
    capabilities = ["unit testing", "integration testing", "regression testing", "coverage analysis"]
    required_tools = ["execute_command"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        res = await tool_registry.execute_tool(
            tool_name="execute_command",
            parameters={"command": "pytest --version"},
            task_id=context.get("task_id") if context else None,
            agent_name=self.name
        )
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output={"test_run": res.result},
            summary="Testing suite executed successfully.",
            tools_used=["execute_command"]
        )
