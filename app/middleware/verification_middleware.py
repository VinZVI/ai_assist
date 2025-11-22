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
            # Allow text messages (non-commands) for conversation
            if command:
                # Allow commands in the allowed_commands list
                if command.split()[0] in allowed_commands:
                    return await handler(event, data)
                # Allow non-command text messages for conversation
                elif not command.startswith("/"):
                    return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            callback_data = event.data
            if callback_data and (
                callback_data in allowed_callbacks
                or any(
                    callback_data.startswith(prefix)
                    for prefix in allowed_callback_prefixes
                )
            ):
                return await handler(event, data)

        # Check verification for other commands/callbacks
        if not user.is_fully_verified:
            await self.handle_unverified_user(event, user)
            return None

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
