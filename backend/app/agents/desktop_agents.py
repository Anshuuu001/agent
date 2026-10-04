from typing import Dict, Any, Optional
from backend.app.schemas.common import AgentCategory
from backend.app.schemas.agents import AgentExecutionResult
from backend.app.core.agent_registry import BaseAgent
from backend.app.core.tool_registry import tool_registry

class DesktopAgent(BaseAgent):
    name = "Desktop Agent"
    display_name = "Desktop OS & Window Controller"
    description = "Controls windows, application focuses, UI workflows, and OS level interactions."
    category = AgentCategory.AUTOMATION
    version = "1.0.0"
    capabilities = ["window management", "app launch", "app close", "ui focus", "desktop monitoring"]
    required_tools = ["take_screenshot", "manage_windows"]
    permissions = ["DESKTOP_CONTROL"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        res = await tool_registry.execute_tool(
            tool_name="manage_windows",
            parameters={"action": "list"},
            task_id=context.get("task_id") if context else None,
            agent_name=self.name
        )
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output=res.result,
            summary=f"Desktop agent managed window focus for: {instruction}",
            tools_used=["manage_windows"]
        )


class BrowserAgent(BaseAgent):
    name = "Browser Agent"
    display_name = "Autonomous Web Navigator Agent"
    description = "Navigates websites, extracts unstructured web data, interacts with web apps safely."
    category = AgentCategory.AUTOMATION
    version = "1.0.0"
    capabilities = ["web navigation", "web research", "multi-page extraction", "form interaction", "file downloads"]
    required_tools = ["search_web", "read_page"]
    permissions = ["NETWORK_ACCESS"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        res = await tool_registry.execute_tool(
            tool_name="search_web",
            parameters={"query": instruction},
            task_id=context.get("task_id") if context else None,
            agent_name=self.name
        )
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output=res.result,
            summary="Web navigation and data extraction finished.",
            tools_used=["search_web"]
        )


class FileAgent(BaseAgent):
    name = "File Agent"
    display_name = "File Management & Organization Agent"
    description = "Catalogs files, organizes folders, converts file types, and manages storage."
    category = AgentCategory.OFFICE
    version = "1.0.0"
    capabilities = ["list files", "categorize files", "move files", "rename files", "create folders", "search directory"]
    required_tools = ["list_files", "search_files", "move_file", "create_folder"]
    permissions = ["FILE_SYSTEM"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        list_res = await tool_registry.execute_tool(
            tool_name="list_files",
            parameters={"path": "."},
            task_id=context.get("task_id") if context else None,
            agent_name=self.name
        )
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output=list_res.result,
            summary=f"File agent processed directory operation: {instruction}",
            tools_used=["list_files"]
        )


class VisionAgent(BaseAgent):
    name = "Vision Agent"
    display_name = "Computer Vision & OCR Agent"
    description = "Analyzes visual screenshots, detects UI controls, buttons, dialogues, and parses on-screen text."
    category = AgentCategory.AUTOMATION
    version = "1.0.0"
    capabilities = ["screenshot analysis", "ocr", "ui element detection", "screen understanding"]
    required_tools = ["take_screenshot", "analyze_screenshot"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        res = await tool_registry.execute_tool(
            tool_name="analyze_screenshot",
            parameters={},
            task_id=context.get("task_id") if context else None,
            agent_name=self.name
        )
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output=res.result,
            summary="Vision agent parsed on-screen UI elements.",
            tools_used=["analyze_screenshot"]
        )
