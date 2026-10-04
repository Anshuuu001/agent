import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.app.schemas.common import ToolCategory, RiskLevel, PermissionLevel
from backend.app.schemas.tools import ToolExecuteResponse
from backend.app.core.security import security_manager
from backend.app.core.audit import audit_logger
from backend.app.db.database import AsyncSessionLocal
from backend.app.db.models import Tool as ToolModel, ToolExecution as ToolExecutionModel, Approval as ApprovalModel

logger = logging.getLogger("desktop_ai.tools")

class BaseTool(ABC):
    name: str
    display_name: str
    description: str
    category: ToolCategory
    risk_level: RiskLevel = RiskLevel.LOW
    permission_level: PermissionLevel = PermissionLevel.READ
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}
    supported_platforms: List[str] = ["windows", "darwin", "linux"]

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the tool action."""
        pass

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category.value,
            "risk_level": self.risk_level.value,
            "permission_level": self.permission_level.value,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "supported_platforms": self.supported_platforms
        }


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name} [{tool.category.value}] (Risk: {tool.risk_level.value})")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self, category: Optional[ToolCategory] = None) -> List[Dict[str, Any]]:
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return [t.get_metadata() for t in tools]

    def find_tools_by_capability(self, capability: str) -> List[BaseTool]:
        """Find tools whose name or description matches capability."""
        cap = capability.lower()
        matches = []
        for tool in self._tools.values():
            if cap in tool.name.lower() or cap in tool.description.lower():
                matches.append(tool)
        return matches

    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        task_id: Optional[str] = None,
        subtask_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        user_confirmed: bool = False
    ) -> ToolExecuteResponse:
        """
        Main tool execution entrypoint:
        1. Validates existence
        2. Security & permission checks (Autonomy level & Emergency stop)
        3. Creates Approval request if required
        4. Executes tool safely
        5. Logs audit trail & persists tool execution record
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolExecuteResponse(
                tool_name=tool_name,
                status="FAILED",
                error=f"Tool '{tool_name}' not found in registry.",
                risk_level=RiskLevel.LOW
            )

        # Security check
        is_allowed, requires_approval, reason = security_manager.check_permission(
            action=tool.name,
            risk_level=tool.risk_level,
            user_confirmed=user_confirmed
        )

        if not is_allowed:
            await audit_logger.log_action(
                action=f"TOOL_BLOCKED:{tool_name}",
                parameters=parameters,
                risk_level=tool.risk_level.value,
                agent_name=agent_name,
                tool_name=tool_name,
                task_id=task_id,
                result_summary="Action blocked by security policy / emergency stop.",
                approval_status="BLOCKED"
            )
            return ToolExecuteResponse(
                tool_name=tool_name,
                status="BLOCKED",
                error=reason,
                risk_level=tool.risk_level
            )

        if requires_approval and not user_confirmed:
            # Create Approval entry
            approval_id = await self._create_approval_request(
                task_id=task_id,
                subtask_id=subtask_id,
                tool_name=tool_name,
                risk_level=tool.risk_level.value,
                reason=reason,
                parameters=parameters
            )
            return ToolExecuteResponse(
                tool_name=tool_name,
                status="REQUIRES_APPROVAL",
                risk_level=tool.risk_level,
                requires_approval=True,
                approval_id=approval_id,
                error=reason
            )

        # Execution
        start_time = time.time()
        status = "SUCCESS"
        error_msg = None
        result_data = {}

        try:
            result_data = await tool.execute(parameters, context={"task_id": task_id, "agent_name": agent_name})
        except Exception as e:
            status = "FAILED"
            error_msg = str(e)
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)

        exec_time_ms = round((time.time() - start_time) * 1000, 2)

        # Persist audit log
        audit_id = await audit_logger.log_action(
            action=f"TOOL_EXECUTE:{tool_name}",
            parameters=parameters,
            risk_level=tool.risk_level.value,
            agent_name=agent_name,
            tool_name=tool_name,
            task_id=task_id,
            result_summary=error_msg or f"Execution completed in {exec_time_ms}ms",
            approval_status="USER_APPROVED" if user_confirmed else "AUTO_APPROVED"
        )

        # Persist tool execution record
        try:
            async with AsyncSessionLocal() as session:
                exec_record = ToolExecutionModel(
                    task_id=task_id,
                    subtask_id=subtask_id,
                    tool_name=tool_name,
                    agent_name=agent_name,
                    input_parameters_json=str(security_manager.redact_secrets(parameters)),
                    output_result_json=str(security_manager.redact_secrets(result_data)),
                    status=status,
                    execution_time_ms=exec_time_ms,
                    risk_level=tool.risk_level.value,
                    error=error_msg,
                    timestamp=datetime.now(timezone.utc)
                )
                session.add(exec_record)
                await session.commit()
        except Exception as db_err:
            logger.error(f"Failed to record tool execution to DB: {db_err}")

        return ToolExecuteResponse(
            tool_name=tool_name,
            status=status,
            result=result_data,
            error=error_msg,
            execution_time_ms=exec_time_ms,
            risk_level=tool.risk_level,
            audit_id=audit_id
        )

    async def _create_approval_request(
        self,
        task_id: Optional[str],
        subtask_id: Optional[str],
        tool_name: str,
        risk_level: str,
        reason: str,
        parameters: Dict[str, Any]
    ) -> str:
        async with AsyncSessionLocal() as session:
            approval = ApprovalModel(
                task_id=task_id or "global",
                subtask_id=subtask_id,
                tool_name=tool_name,
                risk_level=risk_level,
                reason=reason,
                status="PENDING",
                details_json=str(security_manager.redact_secrets(parameters)),
                requested_at=datetime.now(timezone.utc)
            )
            session.add(approval)
            await session.commit()
            await session.refresh(approval)
            return approval.id

tool_registry = ToolRegistry()
