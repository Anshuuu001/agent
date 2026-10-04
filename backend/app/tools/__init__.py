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
from backend.app.tools.browser_tools import (
    SearchWebTool, ReadPageTool
)
from backend.app.tools.vision_tools import (
    AnalyzeScreenTool
)
from backend.app.tools.content_tools import (
    GenerateContentTool, RenderDiagramTool, CreateWordDocumentTool, VerifyFileOutputTool, VerifyResultsTool
)

def register_default_tools():
    """Register all standard built-in tools."""
    tools_to_register = [
        # File tools
        ListFilesTool(),
        SearchFilesTool(),
        ReadFileTool(),
        WriteFileTool(),
        CreateFolderTool(),
        MoveFileTool(),
        # System tools
        GetSystemInfoTool(),
        ListProcessesTool(),
        ExecuteCommandTool(),
        # Desktop tools
        ScreenshotTool(),
        WindowManagementTool(),
        # Browser tools
        SearchWebTool(),
        ReadPageTool(),
        # Vision tools
        AnalyzeScreenTool(),
        # Content, Document, and QA tools
        GenerateContentTool(),
        RenderDiagramTool(),
        CreateWordDocumentTool(),
        VerifyFileOutputTool(),
        VerifyResultsTool(),
    ]
    for t in tools_to_register:
        tool_registry.register(t)

# Automatically register on import
register_default_tools()
