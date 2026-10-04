from typing import List, Optional
from fastapi import APIRouter, HTTPException
from backend.app.schemas.common import ToolCategory
from backend.app.schemas.tools import ToolExecuteRequest, ToolExecuteResponse
from backend.app.core.tool_registry import tool_registry

router = APIRouter(prefix="/tools", tags=["Tools"])

@router.get("")
async def list_tools(category: Optional[ToolCategory] = None):
    """List all registered desktop, file, system, and application tools."""
    return tool_registry.list_tools(category=category)

@router.get("/{tool_name}")
async def get_tool_details(tool_name: str):
    tool = tool_registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    return tool.get_metadata()

@router.post("/execute", response_model=ToolExecuteResponse)
async def execute_tool(payload: ToolExecuteRequest):
    """Execute a registered tool with security clearance and audit logging."""
    return await tool_registry.execute_tool(
        tool_name=payload.tool_name,
        parameters=payload.parameters,
        task_id=payload.task_id,
        subtask_id=payload.subtask_id,
        agent_name=payload.agent_name,
        user_confirmed=payload.bypass_approval_if_allowed
    )
