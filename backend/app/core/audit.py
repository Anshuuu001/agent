import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from backend.app.core.security import security_manager
from backend.app.core.events import event_bus
from backend.app.db.database import AsyncSessionLocal
from backend.app.db.models import AuditLog

logger = logging.getLogger("desktop_ai.audit")

class AuditLogger:
    async def log_action(
        self,
        action: str,
        parameters: Dict[str, Any],
        risk_level: str = "LOW",
        agent_name: Optional[str] = None,
        tool_name: Optional[str] = None,
        task_id: Optional[str] = None,
        result_summary: Optional[str] = None,
        approval_status: str = "AUTO_APPROVED",
        user_ip: str = "127.0.0.1"
    ) -> str:
        """
        Record a sanitized, audit-trailed action into both DB and live event stream.
        """
        safe_params = security_manager.redact_secrets(parameters)
        safe_result = security_manager.redact_secrets(result_summary) if result_summary else None

        audit_entry_id = None
        try:
            async with AsyncSessionLocal() as session:
                entry = AuditLog(
                    task_id=task_id,
                    agent_name=agent_name,
                    tool_name=tool_name,
                    action=action,
                    parameters_safe_json=json.dumps(safe_params),
                    result_summary=safe_result,
                    risk_level=risk_level,
                    approval_status=approval_status,
                    user_ip=user_ip,
                    is_redacted=True,
                    timestamp=datetime.now(timezone.utc)
                )
                session.add(entry)
                await session.commit()
                await session.refresh(entry)
                audit_entry_id = entry.id
        except Exception as e:
            logger.error(f"Failed to write audit log to database: {e}")

        # Broadcast live audit event
        audit_dict = {
            "id": audit_entry_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "agent_name": agent_name,
            "tool_name": tool_name,
            "task_id": task_id,
            "risk_level": risk_level,
            "approval_status": approval_status,
            "parameters": safe_params,
            "result_summary": safe_result
        }
        await event_bus.emit_audit_entry(audit_dict)
        return audit_entry_id or "local"

audit_logger = AuditLogger()
