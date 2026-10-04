import re
import logging
from typing import Dict, Any, Tuple
from backend.app.schemas.common import RiskLevel, AutonomyLevel
from backend.app.config import settings

logger = logging.getLogger("desktop_ai.security")

# Regex patterns for sensitive data redaction
SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey|secret|token|password|passwd|auth[_-]?token|bearer)\s*[:=]\s*["\']?([^"\'\s,;]{6,})["\']?', r'\1: [REDACTED]'),
    (r'(?i)(sk-[a-zA-Z0-9]{20,})', r'sk-[REDACTED]'),
    (r'(?i)(ghp_[a-zA-Z0-9]{20,})', r'ghp_[REDACTED]'),
    (r'(?i)(eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,})', r'[JWT_REDACTED]'),
]

class SecurityManager:
    def __init__(self):
        self._emergency_stop: bool = settings.EMERGENCY_STOP_ACTIVE
        self._current_autonomy_level: AutonomyLevel = AutonomyLevel(settings.DEFAULT_AUTONOMY_LEVEL)

    @property
    def is_emergency_stop_active(self) -> bool:
        return self._emergency_stop

    def trigger_emergency_stop(self) -> None:
        """Immediately prevent all new actions and halt active pipelines."""
        self._emergency_stop = True
        logger.warning("EMERGENCY STOP TRIGGERED. All new actions and tool executions are now BLOCKED.")

    def resume_from_emergency_stop(self) -> None:
        """Clear emergency stop flag."""
        self._emergency_stop = False
        logger.info("Emergency stop cleared by user.")

    def set_autonomy_level(self, level: int) -> None:
        if level in [1, 2, 3, 4]:
            self._current_autonomy_level = AutonomyLevel(level)
            logger.info(f"Autonomy level updated to {self._current_autonomy_level.name} (Level {level})")
        else:
            raise ValueError(f"Invalid autonomy level: {level}. Must be 1, 2, 3, or 4.")

    def get_autonomy_level(self) -> AutonomyLevel:
        return self._current_autonomy_level

    def check_permission(self, action: str, risk_level: RiskLevel, user_confirmed: bool = False) -> Tuple[bool, bool, str]:
        """
        Determines if an action is allowed, and if approval is required.
        Returns: (is_allowed, requires_approval, reason)
        """
        if self._emergency_stop:
            return False, False, "Emergency stop is currently active. All actions are blocked."

        level = self._current_autonomy_level

        # Level 1 — ASSISTED: Asks before almost everything (except LOW risk read operations)
        if level == AutonomyLevel.ASSISTED:
            if risk_level == RiskLevel.LOW and ("read" in action.lower() or "list" in action.lower() or "info" in action.lower()):
                return True, False, "Auto-approved for low-risk read in Assisted mode."
            if user_confirmed:
                return True, False, "Approved by user in Assisted mode."
            return True, True, f"Assisted mode requires explicit confirmation for action '{action}' ({risk_level.value} risk)."

        # Level 2 — SUPERVISED: Executes normal actions automatically, asks for sensitive (HIGH/CRITICAL)
        elif level == AutonomyLevel.SUPERVISED:
            if risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]:
                return True, False, "Auto-approved for normal operation in Supervised mode."
            if user_confirmed:
                return True, False, "Approved by user in Supervised mode."
            return True, True, f"Supervised mode requires approval for {risk_level.value} risk action '{action}'."

        # Level 3 — AUTONOMOUS: Executes most tasks independently, asks only for CRITICAL risk
        elif level == AutonomyLevel.AUTONOMOUS:
            if risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]:
                return True, False, "Auto-approved in Autonomous mode."
            if user_confirmed:
                return True, False, "Approved by user in Autonomous mode."
            return True, True, f"Autonomous mode requires approval for CRITICAL risk action '{action}'."

        # Level 4 — FULL WORKFLOW: Long running with only critical destructive approvals
        elif level == AutonomyLevel.FULL_WORKFLOW:
            if risk_level == RiskLevel.CRITICAL and not user_confirmed:
                return True, True, f"Full Workflow requires approval for irreversible action '{action}'."
            return True, False, "Auto-approved in Full Workflow mode."

        return True, False, "Allowed"

    def redact_secrets(self, text_or_dict: Any) -> Any:
        """Sanitizes text or nested dicts/lists to remove secrets, tokens, and passwords."""
        if isinstance(text_or_dict, str):
            redacted = text_or_dict
            for pattern, repl in SECRET_PATTERNS:
                redacted = re.sub(pattern, repl, redacted)
            return redacted
        elif isinstance(text_or_dict, dict):
            sanitized = {}
            for k, v in text_or_dict.items():
                if any(sec in k.lower() for sec in ["password", "secret", "token", "api_key", "apikey", "credential", "auth"]):
                    sanitized[k] = "[REDACTED_SECRET]"
                else:
                    sanitized[k] = self.redact_secrets(v)
            return sanitized
        elif isinstance(text_or_dict, list):
            return [self.redact_secrets(item) for item in text_or_dict]
        return text_or_dict

security_manager = SecurityManager()
