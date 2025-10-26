"""Consent management for user onboarding and legal agreements."""

from datetime import datetime
from enum import Enum
from typing import Optional

from loguru import logger
from pydantic import BaseModel

from app.compliance.age_verification import AgeVerificationService
from app.config import get_config
from app.models.user import User
from app.services.user_service import UserService


class OnboardingState(Enum):
    """States for the user onboarding process."""

    NOT_STARTED = "not_started"
    SHOWING_WELCOME = "showing_welcome"
    AWAITING_CONSENT = "awaiting_consent"
    COMPLETED = "completed"
    FAILED = "failed"


class ConsentResult(BaseModel):
    """Result of a consent action."""

    success: bool
    next_state: OnboardingState
    message: str
    show_keyboard: bool = True


class ConsentType(Enum):
    """Types of consent that can be given."""

    TERMS = "terms"
    PRIVACY = "privacy"
    GUIDELINES = "guidelines"
    FULL_CONSENT = "full_consent"


class ConsentManager:
    """Manager for handling user consent processes."""

    def __init__(
        self,
        user_service: UserService,
        age_verification_service: AgeVerificationService,
    ):
        self.user_service = user_service
        self.age_verification_service = age_verification_service
        self.config = get_config()
        self.current_versions = {
            "terms": self.config.compliance.terms_version,
            "privacy": self.config.compliance.privacy_version,
            "guidelines": self.config.compliance.guidelines_version,
        }

    async def start_onboarding_flow(
        self, user_id: int, ip_address: str | None = None
    ) -> OnboardingState:
        """
        Start the onboarding flow for a user.

        Args:
            user_id: The Telegram user ID
            ip_address: IP address for audit purposes

        Returns:
            OnboardingState: The initial state for the onboarding process
        """
        try:
            user = await self.user_service.get_user_by_telegram_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found for onboarding")
                return OnboardingState.FAILED

            # Check if user is already fully verified
            if user.is_fully_verified:
                return OnboardingState.COMPLETED

            logger.info(f"Starting onboarding flow for user {user_id}")
            return OnboardingState.SHOWING_WELCOME

        except Exception as e:
            logger.error(f"Error starting onboarding flow for user {user_id}: {e}")
            return OnboardingState.FAILED

    async def process_consent_response(
        self,
        user_id: int,
        consent_type: str,
        accepted: bool,
        ip_address: str | None = None,
    ) -> ConsentResult:
        """
        Process a user's response to a consent request.

        Args:
            user_id: The Telegram user ID
            consent_type: Type of consent being responded to
            accepted: Whether the user accepted the consent
            ip_address: IP address for audit purposes

        Returns:
            ConsentResult: The result of processing the consent response
        """
        try:
            user = await self.user_service.get_user_by_telegram_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found for consent processing")
                return ConsentResult(
                    success=False,
                    next_state=OnboardingState.FAILED,
                    message="User not found",
                )

            # Handle consent rejection
            if not accepted:
                logger.info(f"User {user_id} rejected consent")
                return ConsentResult(
                    success=True,  # Successfully processed, even though rejected
                    next_state=OnboardingState.FAILED,
                    message="Registration rejected. You must accept all terms to use this service.",
                )

            # Handle different types of consent
            if consent_type == "full_consent":
                # Update all consent fields
                user.terms_accepted = True
                user.privacy_policy_accepted = True
                user.community_guidelines_accepted = True
                user.terms_version = self.current_versions["terms"]
                user.privacy_version = self.current_versions["privacy"]
                user.guidelines_version = self.current_versions["guidelines"]
                user.consent_timestamp = datetime.utcnow()
                if ip_address:
                    user.consent_ip_address = ip_address

                # Mark as verified
                user.verification_status = "verified"

                # Save the updated user
                await self.user_service.update_user(user)

                logger.info(f"User {user_id} completed full consent process")
                return ConsentResult(
                    success=True,
                    next_state=OnboardingState.COMPLETED,
                    message="Registration completed successfully! You can now use all features.",
                )

            # For specific consent types (terms, privacy, guidelines)
            consent_updated = False
            if consent_type == "terms":
                user.terms_accepted = True
                user.terms_version = self.current_versions["terms"]
                consent_updated = True
            elif consent_type == "privacy":
                user.privacy_policy_accepted = True
                user.privacy_version = self.current_versions["privacy"]
                consent_updated = True
            elif consent_type == "guidelines":
                user.community_guidelines_accepted = True
                user.guidelines_version = self.current_versions["guidelines"]
                consent_updated = True

            if consent_updated:
                user.consent_timestamp = datetime.utcnow()
                if ip_address:
                    user.consent_ip_address = ip_address
                await self.user_service.update_user(user)

                logger.info(f"User {user_id} accepted {consent_type}")
                return ConsentResult(
                    success=True,
                    next_state=OnboardingState.AWAITING_CONSENT,  # May need more consents
                    message=f"Consent for {consent_type} accepted",
                )

            # If we get here, it's an unknown consent type
            logger.warning(f"Unknown consent type '{consent_type}' for user {user_id}")
            return ConsentResult(
                success=False,
                next_state=OnboardingState.FAILED,
                message="Invalid consent type",
            )

        except Exception as e:
            logger.error(f"Error processing consent response for user {user_id}: {e}")
            return ConsentResult(
                success=False,
                next_state=OnboardingState.FAILED,
                message="An error occurred while processing your consent",
            )

    async def check_verification_status(self, user_id: int) -> str:
        """
        Check the verification status of a user.

        Args:
            user_id: The Telegram user ID

        Returns:
            str: The verification status
        """
        try:
            user = await self.user_service.get_user_by_telegram_id(user_id)
            if not user:
                return "not_found"

            return user.verification_status

        except Exception as e:
            logger.error(f"Error checking verification status for user {user_id}: {e}")
            return "error"

    async def is_onboarding_required(self, user_id: int) -> bool:
        """
        Check if a user needs to complete onboarding.

        Args:
            user_id: The Telegram user ID

        Returns:
            bool: True if onboarding is required
        """
        try:
            user = await self.user_service.get_user_by_telegram_id(user_id)
            if not user:
                # If user doesn't exist, they need onboarding
                return True

            # Check if user is already fully verified
            return not user.is_fully_verified

        except Exception as e:
            logger.error(
                f"Error checking onboarding requirement for user {user_id}: {e}"
            )
            # If there's an error, assume onboarding is required for safety
            return True

    async def complete_verification(self, user_id: int) -> bool:
        """
        Complete the verification process for a user.

        Args:
            user_id: The Telegram user ID

        Returns:
            bool: True if verification was completed successfully
        """
        try:
            user = await self.user_service.get_user_by_telegram_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found for verification completion")
                return False

            # Mark as verified
            user.verification_status = "verified"
            await self.user_service.update_user(user)

            logger.info(f"Verification completed for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error completing verification for user {user_id}: {e}")
            return False
