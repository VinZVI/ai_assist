"""Verification middleware for checking user verification status."""

from collections.abc import Awaitable, Callable
from typing import Any, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from loguru import logger

from app.compliance.consent_manager import ConsentManager
from app.models.user import User
from app.services.user_service import UserService


class VerificationMiddleware(BaseMiddleware):
    """Middleware for checking user verification status."""

    def __init__(self, consent_manager: ConsentManager):
        self.consent_manager = consent_manager

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Get user from context
        user: User = data.get("user")

        if not user:
            logger.info(
                "VerificationMiddleware: No user in context, allowing event to proceed"
            )
            return await handler(event, data)

        # List of commands available without verification
        allowed_commands = ["/start", "/help", "/support"]

        # List of callback data available without verification
        allowed_callbacks = [
            "start_chat",
            "my_stats",
            "premium_info",
            "help",
            "settings",
            "main_menu",
        ]

        # List of callback prefixes available without verification
        allowed_callback_prefixes = [
            "onboarding:",
            "consent:",
            "select_language:",
            "buy_premium:",
        ]

        # Check event type
        if isinstance(event, Message):
            command = event.text
            logger.info(
                f"VerificationMiddleware: Processing message with text: {command}"
            )
            # Allow text messages (non-commands) for conversation
            if command:
                # Allow commands in the allowed_commands list
                if command.split()[0] in allowed_commands:
                    logger.info(
                        f"VerificationMiddleware: Allowing command '{command}' to proceed"
                    )
                    return await handler(event, data)
                # Allow non-command text messages for conversation
                if not command.startswith("/"):
                    logger.info(
                        "VerificationMiddleware: Allowing non-command message to proceed"
                    )
                    return await handler(event, data)
                logger.info(
                    f"VerificationMiddleware: Command '{command}' requires verification"
                )
        elif isinstance(event, CallbackQuery):
            callback_data = event.data
            logger.info(
                f"VerificationMiddleware: Processing callback with data: {callback_data}"
            )

            # Check if callback data is allowed
            is_allowed = False
            if callback_data:
                # Direct match
                if callback_data in allowed_callbacks:
                    is_allowed = True
                    logger.info(
                        f"VerificationMiddleware: Callback data '{callback_data}' is in allowed_callbacks"
                    )

                # Prefix match
                for prefix in allowed_callback_prefixes:
                    if callback_data.startswith(prefix):
                        is_allowed = True
                        logger.info(
                            f"VerificationMiddleware: Callback data '{callback_data}' starts with allowed prefix '{prefix}'"
                        )
                        break

            if is_allowed:
                logger.info(
                    f"VerificationMiddleware: Allowing callback '{callback_data}' to proceed"
                )
                return await handler(event, data)
            logger.info(
                f"VerificationMiddleware: Callback '{callback_data}' not allowed, checking verification status"
            )

        # Check verification for other commands/callbacks
        logger.info(
            f"VerificationMiddleware: Checking verification status for user {user.telegram_id}"
        )
        logger.info(f"  User verification_status: {user.verification_status}")
        logger.info(f"  User is_fully_verified: {user.is_fully_verified}")

        if not user.is_fully_verified:
            logger.info(
                f"VerificationMiddleware: User {user.telegram_id} is not fully verified, handling accordingly"
            )
            await self.handle_unverified_user(event, user)
            return None

        logger.info(
            f"VerificationMiddleware: User {user.telegram_id} is fully verified, allowing to proceed"
        )
        return await handler(event, data)

    async def handle_unverified_user(self, event: TelegramObject, user: User):
        """Handle unverified user."""

        message_text = """
⚠️ Для использования бота необходимо пройти регистрацию.

Используйте команду /start для начала регистрации.
"""

        if isinstance(event, Message):
            await event.answer(message_text)
        elif isinstance(event, CallbackQuery):
            await event.message.answer(message_text)
            await event.answer()


async def setup_verification_middleware(
    user_service: UserService,
) -> VerificationMiddleware:
    """Setup the verification middleware with dependencies."""

    # Import here to avoid circular imports
    from app.compliance.age_verification import AgeVerificationService

    # Create services
    age_verification_service = AgeVerificationService(user_service)
    consent_manager = ConsentManager(user_service, age_verification_service)

    return VerificationMiddleware(consent_manager)
