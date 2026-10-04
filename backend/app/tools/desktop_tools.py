import base64
import io
import logging
from typing import Dict, Any
from backend.app.schemas.common import ToolCategory, RiskLevel, PermissionLevel
from backend.app.core.tool_registry import BaseTool

logger = logging.getLogger("desktop_ai.desktop_tools")

class ScreenshotTool(BaseTool):
    name = "take_screenshot"
    display_name = "Capture Desktop Screenshot"
    description = "Capture image of full desktop or active window."
    category = ToolCategory.DESKTOP
    risk_level = RiskLevel.LOW
    permission_level = PermissionLevel.READ

    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            buffered = io.BytesIO()
            screenshot.save(buffered, format="JPEG", quality=75)
            img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            return {
                "width": screenshot.width,
                "height": screenshot.height,
                "format": "JPEG",
                "image_base64_preview": f"data:image/jpeg;base64,{img_b64[:100]}... (truncated for brevity)",
                "image_data": img_b64
            }
        except Exception as e:
            return {"error": f"Screenshot capture error: {e}"}


class WindowManagementTool(BaseTool):
    name = "manage_windows"
    display_name = "Window Management"
    description = "List, focus, minimize, or bring desktop windows to foreground."
    category = ToolCategory.DESKTOP
    risk_level = RiskLevel.LOW
    permission_level = PermissionLevel.EXECUTE

    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        action = parameters.get("action", "list")
        target_title = parameters.get("title", "")
        
        try:
            import pygetwindow as gw
            windows = gw.getAllTitles()
            filtered = [w for w in windows if w.strip()]
            return {
                "action": action,
                "open_windows_count": len(filtered),
                "windows": filtered[:20]
            }
        except Exception as e:
            return {"error": f"Window management: {e}"}
