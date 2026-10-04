from backend.app.core.tool_registry import tool_registry
from backend.app.tools.file_tools import (
    ListFilesTool, SearchFilesTool, ReadFileTool, WriteFileTool, CreateFolderTool, MoveFileTool
)
from backend.app.tools.system_tools import (
    GetSystemInfoTool, ListProcessesTool, ExecuteCommandTool
)
from backend.app.tools.desktop_tools import (
    ScreenshotTool, WindowManagementTool
)
from backend.app.tools.desktop_control_tools import (
    LaunchApplicationTool, FocusWindowTool, MouseClickTool, KeyboardTypeTool
)
from backend.app.tools.real_browser_tools import (
    RealWebSearchTool, RealWebScraperTool
)
from backend.app.tools.vision_tools import (
    AnalyzeScreenTool
)
from backend.app.tools.content_tools import (
    GenerateContentTool, RenderDiagramTool, VerifyFileOutputTool, VerifyResultsTool
)
from backend.app.tools.document_engine_tools import (
    CreateRealWordProjectDocumentTool
)

def register_default_tools():
    """Register all standard built-in and advanced tools."""
    tools_to_register = [
        # File tools
        ListFilesTool(),
        SearchFilesTool(),
        ReadFileTool(),
        WriteFileTool(),
        CreateFolderTool(),
        MoveFileTool(),
        # System & Shell tools
        GetSystemInfoTool(),
        ListProcessesTool(),
        ExecuteCommandTool(),
        # Windows & Desktop Control tools
        ScreenshotTool(),
        WindowManagementTool(),
        LaunchApplicationTool(),
        FocusWindowTool(),
        MouseClickTool(),
        KeyboardTypeTool(),
        # Real Browser & Web Scraping tools
        RealWebSearchTool(),
        RealWebScraperTool(),
        # Vision tools
        AnalyzeScreenTool(),
        # Real Document, Diagram & QA verification tools
        GenerateContentTool(),
        RenderDiagramTool(),
        CreateRealWordProjectDocumentTool(),
        VerifyFileOutputTool(),
        VerifyResultsTool(),
    ]
    for t in tools_to_register:
        tool_registry.register(t)

# Automatically register on import
register_default_tools()
