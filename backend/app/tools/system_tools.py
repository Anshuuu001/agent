import sys
import platform
import psutil
import subprocess
import asyncio
from typing import Dict, Any
from backend.app.schemas.common import ToolCategory, RiskLevel, PermissionLevel
from backend.app.core.tool_registry import BaseTool

class GetSystemInfoTool(BaseTool):
    name = "get_system_info"
    display_name = "Get System Information"
    description = "Retrieve OS platform, CPU, memory, and environment stats."
    category = ToolCategory.SYSTEM
    risk_level = RiskLevel.LOW
    permission_level = PermissionLevel.READ

    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        mem = psutil.virtual_memory()
        return {
            "platform": platform.platform(),
            "os": platform.system(),
            "python_version": sys.version.split()[0],
            "cpu_cores": psutil.cpu_count(logical=True),
            "cpu_usage_percent": psutil.cpu_percent(interval=0.1),
            "memory_total_gb": round(mem.total / (1024 ** 3), 2),
            "memory_available_gb": round(mem.available / (1024 ** 3), 2),
            "memory_percent": mem.percent
        }


class ListProcessesTool(BaseTool):
    name = "list_processes"
    display_name = "List Running Processes"
    description = "List currently active desktop processes and windows."
    category = ToolCategory.SYSTEM
    risk_level = RiskLevel.LOW
    permission_level = PermissionLevel.READ

    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = p.info
                if info.get('name') and not info['name'].startswith("System"):
                    procs.append(info)
                    if len(procs) >= 30:
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return {"process_count": len(procs), "processes": procs}


class ExecuteCommandTool(BaseTool):
    name = "execute_command"
    display_name = "Execute System Shell Command"
    description = "Execute a command in system shell with stdout/stderr capture."
    category = ToolCategory.SYSTEM
    risk_level = RiskLevel.HIGH
    permission_level = PermissionLevel.EXECUTE

    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        cmd = parameters.get("command", "")
        if not cmd:
            return {"error": "No command provided"}

        # Asynchronously run subprocess
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return {
            "command": cmd,
            "return_code": proc.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "success": proc.returncode == 0
        }
