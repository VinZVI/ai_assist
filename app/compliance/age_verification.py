"""Age verification functionality for user onboarding."""

from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.user_service import UserService


class AgeVerificationError(Exception):
    """Exception raised for age verification errors."""


class AgeVerificationService:
    """Service for handling age verification processes."""

    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def verify_user_age(
        self, user_id: int, is_adult: bool, ip_address: str | None = None
    ) -> bool:
        """
        Verify a user's age and update their verification status.

        Args:
            user_id: The Telegram user ID
            is_adult: Whether the user has confirmed they are an adult (18+)
            ip_address: IP address for audit purposes

        Returns:
            bool: True if verification was successful, False otherwise
        """
        try:
            # Get the user
            user = await self.user_service.get_user_by_telegram_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found for age verification")
                return False

            # Update age verification status
            user.age_verified = is_adult
            from datetime import UTC, datetime

            user.consent_timestamp = datetime.now(UTC)
            if ip_address:
                user.consent_ip_address = ip_address

            # Save the updated user
            updated_user = await self.user_service.update_user(user)
            if not updated_user:
                logger.error(f"Failed to update user {user_id} for age verification")
                return False

            logger.info(
                f"Age verification {'completed' if is_adult else 'failed'} for user {user_id}"
            )
            return is_adult

        except Exception as e:
            logger.error(f"Error during age verification for user {user_id}: {e}")
            return False

    async def is_age_verification_required(self, user: User) -> bool:
        """
        Check if a user needs to complete age verification.

        Args:
            user: The user to check

        Returns:
            bool: True if age verification is required
        """
        # Age verification is required if not yet verified
        return not user.age_verified

    async def is_user_verified_adult(self, user: User) -> bool:
        """
        Check if a user is verified as an adult.

        Args:
            user: The user to check

        Returns:
            bool: True if user is verified as an adult
        """
        return user.age_verified and user.verification_status == "verified"
