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

        # Check event type
        if isinstance(event, Message):
            command = event.text
            if command and command.split()[0] in allowed_commands:
                return await handler(event, data)

        # Check verification
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
