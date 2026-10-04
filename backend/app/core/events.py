import asyncio
import json
import logging
from typing import Set, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import WebSocket

logger = logging.getLogger("desktop_ai.events")

class EventBus:
    def __init__(self):
        self._active_connections: Set[WebSocket] = set()
        self._subscribers: Dict[str, Set[Any]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self._active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            self._active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Remaining connections: {len(self._active_connections)}")

    async def broadcast(self, event_type: str, data: Dict[str, Any], task_id: Optional[str] = None):
        """Broadcast event to all connected WebSocket clients."""
        payload = {
            "event": event_type,
            "data": data,
            "task_id": task_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        text = json.dumps(payload)
        async with self._lock:
            dead_connections = set()
            for connection in self._active_connections:
                try:
                    await connection.send_text(text)
                except Exception as e:
                    logger.debug(f"Error sending message to websocket: {e}")
                    dead_connections.add(connection)
            
            for dead in dead_connections:
                self._active_connections.discard(dead)

    async def emit_task_update(self, task_id: str, status: str, progress: float, details: Optional[Dict[str, Any]] = None):
        await self.broadcast("task_update", {
            "task_id": task_id,
            "status": status,
            "progress": progress,
            "details": details or {}
        }, task_id=task_id)

    async def emit_agent_status(self, agent_name: str, status: str, current_task: Optional[str] = None, health: str = "HEALTHY"):
        await self.broadcast("agent_status", {
            "agent_name": agent_name,
            "status": status,
            "current_task": current_task,
            "health": health
        })

    async def emit_audit_entry(self, audit_dict: Dict[str, Any]):
        await self.broadcast("audit_log", audit_dict)

    async def emit_notification(self, title: str, message: str, notification_type: str = "INFO", priority: str = "NORMAL"):
        await self.broadcast("notification", {
            "title": title,
            "message": message,
            "type": notification_type,
            "priority": priority
        })

    async def emit_approval_request(self, approval_dict: Dict[str, Any]):
        await self.broadcast("approval_required", approval_dict)

event_bus = EventBus()
