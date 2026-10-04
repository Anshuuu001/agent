import pytest
from backend.app.core.tool_registry import tool_registry
from backend.app.schemas.common import RiskLevel
from backend.app.core.security import security_manager

def test_tool_registry_initialization():
    tools = tool_registry.list_tools()
    assert len(tools) >= 10
    tool_names = [t["name"] for t in tools]
    assert "list_files" in tool_names
    assert "get_system_info" in tool_names
    assert "search_web" in tool_names
    assert "generate_content" in tool_names

@pytest.mark.asyncio
async def test_tool_execution_system_info():
    res = await tool_registry.execute_tool(
        tool_name="get_system_info",
        parameters={}
    )
    assert res.status == "SUCCESS"
    assert "cpu_cores" in res.result
    assert "platform" in res.result

@pytest.mark.asyncio
async def test_tool_execution_blocked_by_emergency_stop():
    security_manager.trigger_emergency_stop()
    try:
        res = await tool_registry.execute_tool(
            tool_name="list_files",
            parameters={"path": "."}
        )
        assert res.status == "BLOCKED"
        assert "Emergency stop" in res.error
    finally:
        security_manager.resume_from_emergency_stop()
