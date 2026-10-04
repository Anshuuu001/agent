import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
from backend.app.schemas.common import ToolCategory, RiskLevel, PermissionLevel
from backend.app.core.tool_registry import BaseTool

class ListFilesTool(BaseTool):
    name = "list_files"
    display_name = "List Files in Directory"
    description = "List all files and folders in a specified path with metadata."
    category = ToolCategory.FILES
    risk_level = RiskLevel.LOW
    permission_level = PermissionLevel.READ
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "default": "."}
        }
    }

    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        target_path = Path(parameters.get("path", ".")).resolve()
        if not target_path.exists():
            return {"error": f"Directory does not exist: {target_path}", "files": []}

        items = []
        for entry in target_path.iterdir():
            items.append({
                "name": entry.name,
                "is_dir": entry.is_dir(),
                "size_bytes": entry.stat().st_size if entry.is_file() else 0,
                "path": str(entry)
            })
        return {"directory": str(target_path), "count": len(items), "items": items[:100]}


class SearchFilesTool(BaseTool):
    name = "search_files"
    display_name = "Search Files"
    description = "Search files matching pattern or text in given directory."
    category = ToolCategory.FILES
    risk_level = RiskLevel.LOW
    permission_level = PermissionLevel.READ

    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        root = Path(parameters.get("path", ".")).resolve()
        pattern = parameters.get("pattern", "*")
        matches = []
        if root.exists():
            for p in root.rglob(pattern):
                if len(matches) >= 50:
                    break
                matches.append({"name": p.name, "path": str(p), "is_file": p.is_file()})
        return {"query_path": str(root), "pattern": pattern, "results": matches}


class ReadFileTool(BaseTool):
    name = "read_file"
    display_name = "Read File Content"
    description = "Read text content of a file."
    category = ToolCategory.FILES
    risk_level = RiskLevel.LOW
    permission_level = PermissionLevel.READ

    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        file_path = Path(parameters.get("file_path", "")).resolve()
        if not file_path.exists():
            return {"error": f"File does not exist: {file_path}"}
        if not file_path.is_file():
            return {"error": f"Path is not a file: {file_path}"}

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            return {"file_path": str(file_path), "size": len(content), "content": content[:20000]}
        except Exception as e:
            return {"error": str(e)}


class WriteFileTool(BaseTool):
    name = "write_file"
    display_name = "Write File"
    description = "Write content to a file. Overwrites or creates as needed."
    category = ToolCategory.FILES
    risk_level = RiskLevel.MEDIUM
    permission_level = PermissionLevel.WRITE

    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        file_path = Path(parameters.get("file_path", "")).resolve()
        content = parameters.get("content", "")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return {"file_path": str(file_path), "bytes_written": len(content), "status": "CREATED"}


class CreateFolderTool(BaseTool):
    name = "create_folder"
    display_name = "Create Folder"
    description = "Create a directory structure."
    category = ToolCategory.FILES
    risk_level = RiskLevel.LOW
    permission_level = PermissionLevel.WRITE

    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        folder_path = Path(parameters.get("folder_path", "")).resolve()
        folder_path.mkdir(parents=True, exist_ok=True)
        return {"folder_path": str(folder_path), "status": "CREATED"}


class MoveFileTool(BaseTool):
    name = "move_file"
    display_name = "Move / Rename File"
    description = "Move or rename a file or directory."
    category = ToolCategory.FILES
    risk_level = RiskLevel.MEDIUM
    permission_level = PermissionLevel.WRITE

    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        src = Path(parameters.get("source_path", "")).resolve()
        dst = Path(parameters.get("destination_path", "")).resolve()
        if not src.exists():
            return {"error": f"Source path does not exist: {src}"}
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return {"source": str(src), "destination": str(dst), "status": "MOVED"}
