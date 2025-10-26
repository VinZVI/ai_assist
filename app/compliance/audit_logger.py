"""Audit logging for compliance events."""

import json
from datetime import datetime
from typing import Any, Optional

from loguru import logger


class ComplianceLogger:
    """Specialized logging for compliance and verification events."""

    @staticmethod
    def log_consent_action(
        user_id: int,
        action: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Log consent actions for audit purposes.

        Args:
            user_id: The Telegram user ID
            action: The consent action (accept, reject, etc.)
            ip_address: IP address for audit purposes
            user_agent: User agent string
        """
        audit_data = {
            "event_type": "consent_action",
            "user_id": user_id,
            "action": action,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Structured log for audit
        logger.info("COMPLIANCE_AUDIT", extra=audit_data)

    @staticmethod
    def log_verification_attempt(
        user_id: int, success: bool, reason: str | None = None
    ) -> None:
        """
        Log verification attempts.

        Args:
            user_id: The Telegram user ID
            success: Whether the verification was successful
            reason: Reason for failure (if applicable)
        """
        audit_data = {
            "event_type": "verification_attempt",
            "user_id": user_id,
            "success": success,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info("VERIFICATION_AUDIT", extra=audit_data)

    @staticmethod
    def log_onboarding_event(
        user_id: int, event: str, details: dict[str, Any] | None = None
    ) -> None:
        """
        Log onboarding events.

        Args:
            user_id: The Telegram user ID
            event: The onboarding event
            details: Additional details about the event
        """
        audit_data = {
            "event_type": "onboarding_event",
            "user_id": user_id,
            "event": event,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info("ONBOARDING_AUDIT", extra=audit_data)
