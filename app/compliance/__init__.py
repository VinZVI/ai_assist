"""Compliance package for age verification and consent management."""

from .age_verification import AgeVerificationService
from .audit_logger import ComplianceLogger
from .consent_manager import ConsentManager
from .legal_texts import LegalTexts

__all__ = [
    "AgeVerificationService",
    "ComplianceLogger",
    "ConsentManager",
    "LegalTexts",
]
