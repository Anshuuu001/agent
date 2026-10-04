import os
import sys
import subprocess
import shutil
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.app.schemas.common import ToolCategory, RiskLevel, PermissionLevel
from backend.app.core.tool_registry import BaseTool

logger = logging.getLogger("desktop_ai.desktop_control")

# Common Windows App executables and URI protocols
APP_MAPPINGS = {
    "word": ["winword", "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE", "C:\\Program Files (x86)\\Microsoft Office\\root\\Office16\\WINWORD.EXE"],
    "excel": ["excel", "C:\\Program Files\\Microsoft Office\\root\\Office16\\EXCEL.EXE"],
    "powerpoint": ["powerpnt", "C:\\Program Files\\Microsoft Office\\root\\Office16\\POWERPNT.EXE"],
    "vscode": ["code", "code.cmd", os.path.expandvars("%LOCALAPPDATA%\\Programs\\Microsoft VS Code\\Code.exe")],
    "chrome": ["chrome", "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"],
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "terminal": ["wt.exe", "powershell.exe", "cmd.exe"],
    "explorer": ["explorer.exe"]
}

class LaunchApplicationTool(BaseTool):
    name = "launch_application"
    display_name = "Launch Desktop Application"
    description = "Opens a desktop application on Windows (e.g. Word, VS Code, Chrome, Notepad, Calculator, Explorer, or custom .exe) with optional file arguments."
    category = ToolCategory.DESKTOP
    risk_level = RiskLevel.LOW
    permission_level = PermissionLevel.EXECUTE

    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        app_name = parameters.get("application", "").lower().strip()
        file_argument = parameters.get("file_path", "")

        candidates = APP_MAPPINGS.get(app_name, [app_name])
        launched_path = None

        for candidate in candidates:
            # Check if command is in PATH or file exists
            resolved = shutil.which(candidate) or (candidate if os.path.exists(candidate) else None)
            if resolved:
                cmd = [resolved]
                if file_argument:
                    cmd.append(str(Path(file_argument).resolve()))
                try:
                    subprocess.Popen(cmd, shell=False)
                    launched_path = resolved
                    break
                except Exception as launch_err:
                    logger.debug(f"Failed candidate {candidate}: {launch_err}")

        # Fallback to start / os.startfile on Windows
        if not launched_path:
            try:
                if file_argument and os.path.exists(file_argument):
                    os.startfile(file_argument)
                    launched_path = f"os.startfile({file_argument})"
                else:
                    os.system(f"start {app_name}")
                    launched_path = f"start {app_name}"
            except Exception as e:
                return {"error": f"Could not launch application '{app_name}': {e}", "status": "FAILED"}

        return {
            "status": "LAUNCHED",
            "application": app_name,
            "executable": launched_path,
            "file_argument": file_argument or None
        }


class FocusWindowTool(BaseTool):
    name = "focus_window"
    display_name = "Focus Desktop Window"
    description = "Brings a target application window to the foreground by title or process name."
    category = ToolCategory.DESKTOP
    risk_level = RiskLevel.LOW
    permission_level = PermissionLevel.EXECUTE

    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        title_query = parameters.get("title", "").lower()
        
        try:
            import pygetwindow as gw
            windows = gw.getAllWindows()
            matched = None
            for w in windows:
                if w.title and title_query in w.title.lower():
                    matched = w
                    break

            if matched:
                try:
                    if matched.isMinimized:
                        matched.restore()
                    matched.activate()
                    return {"status": "FOCUSED", "window_title": matched.title, "found": True}
                except Exception as act_err:
                    # Windows SetForegroundWindow fallback
                    return {"status": "FOCUSED_ATTEMPTED", "window_title": matched.title, "note": str(act_err)}
            else:
                return {"status": "NOT_FOUND", "query": title_query, "open_windows": [w.title for w in windows if w.title][:10]}
        except Exception as e:
            return {"error": f"Focus window error: {e}"}


class MouseClickTool(BaseTool):
    name = "mouse_click"
    display_name = "Mouse Click at Coordinates"
    description = "Moves the mouse cursor to (x, y) coordinates and performs single, double, or right click."
    category = ToolCategory.DESKTOP
    risk_level = RiskLevel.MEDIUM
    permission_level = PermissionLevel.EXECUTE

    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        x = parameters.get("x")
        y = parameters.get("y")
        click_type = parameters.get("click_type", "left").lower()  # left, right, double

        try:
            import pyautogui
            if x is not None and y is not None:
                pyautogui.moveTo(int(x), int(y), duration=0.2)
            
            if click_type == "double":
                pyautogui.doubleClick()
            elif click_type == "right":
                pyautogui.rightClick()
            else:
                pyautogui.click()

            current_pos = pyautogui.position()
            return {"status": "CLICKED", "type": click_type, "position": [current_pos.x, current_pos.y]}
        except Exception as e:
            return {"error": f"Mouse click error: {e}"}


class KeyboardTypeTool(BaseTool):
    name = "keyboard_type"
    display_name = "Type Text & Send Hotkeys"
    description = "Types text with simulated keystrokes or sends keyboard shortcuts (e.g. ['ctrl', 's'], ['alt', 'tab'], ['enter'])."
    category = ToolCategory.DESKTOP
    risk_level = RiskLevel.MEDIUM
    permission_level = PermissionLevel.EXECUTE

    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        text = parameters.get("text")
        hotkeys = parameters.get("hotkeys")  # list of keys e.g. ["ctrl", "s"]
        key = parameters.get("key")          # single key e.g. "enter"

        try:
            import pyautogui
            if hotkeys and isinstance(hotkeys, list):
                pyautogui.hotkey(*hotkeys)
                return {"status": "HOTKEY_SENT", "hotkeys": hotkeys}
            elif key:
                pyautogui.press(key)
                return {"status": "KEY_PRESSED", "key": key}
            elif text:
                pyautogui.write(text, interval=0.02)
                return {"status": "TEXT_TYPED", "length": len(text)}
            else:
                return {"error": "No text, hotkeys, or key provided"}
        except Exception as e:
            return {"error": f"Keyboard error: {e}"}
