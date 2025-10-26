"""Onboarding handler for user registration and verification."""

from collections.abc import Callable
from typing import Any, Dict

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.types.base import TelegramObject
from loguru import logger

from app.compliance.consent_manager import ConsentManager
from app.compliance.legal_texts import LegalTexts
from app.keyboards.onboarding_keyboards import OnboardingKeyboards
from app.models.user import User
from app.services.user_service import UserService

# Create router for onboarding
onboarding_router = Router(name="onboarding")


class OnboardingStates(StatesGroup):
    """States for the onboarding process."""

    WELCOME = State()
    CONSENT = State()
    COMPLETED = State()


class OnboardingHandler:
    """Handler for the onboarding process."""

    def __init__(self, consent_manager: ConsentManager):
        self.consent_manager = consent_manager

    def get_user_ip(self, event: TelegramObject) -> str:
        """Get user IP address from event (stub implementation)."""
        # In a real implementation, you would extract the IP from the request
        # For now, we'll return a placeholder
        return "127.0.0.1"

    async def handle_start_command(
        self, message: Message, user: User, state: FSMContext, **kwargs
    ):
        """Handle the /start command."""

        # Check if onboarding is required
        if not await self.consent_manager.is_onboarding_required(user.telegram_id):
            await message.answer(
                text=LegalTexts.ALREADY_VERIFIED_MESSAGE, parse_mode="HTML"
            )
            return

        # Show welcome message
        await message.answer(
            text=LegalTexts.WELCOME_MESSAGE,
            reply_markup=OnboardingKeyboards.welcome_keyboard(),
            parse_mode="HTML",
        )

        # Set state to WELCOME
        await state.set_state(OnboardingStates.WELCOME)

    async def show_welcome_message(
        self, message: Message, user: User, state: FSMContext
    ):
        """Show the welcome message."""

        await message.answer(
            text=LegalTexts.WELCOME_MESSAGE,
            reply_markup=OnboardingKeyboards.welcome_keyboard(),
            parse_mode="HTML",
        )

        # Set state to WELCOME
        await state.set_state(OnboardingStates.WELCOME)

    async def show_already_verified_message(self, message: Message):
        """Show message for already verified users."""

        await message.answer(
            text=LegalTexts.ALREADY_VERIFIED_MESSAGE, parse_mode="HTML"
        )

    async def handle_onboarding_callback(
        self, callback: CallbackQuery, user: User, state: FSMContext, **kwargs
    ):
        """Handle onboarding callbacks."""

        action = callback.data.split(":")[1]

        if action == "start":
            await callback.message.edit_text(
                text=LegalTexts.CONSENT_TEXT,
                reply_markup=OnboardingKeyboards.consent_keyboard(),
                parse_mode="HTML",
                disable_web_page_preview=True,
            )

            # Set state to CONSENT
            await state.set_state(OnboardingStates.CONSENT)

        elif action == "info":
            await callback.message.edit_text(
                text=LegalTexts.BOT_INFO_MESSAGE,
                reply_markup=OnboardingKeyboards.info_keyboard(),
                parse_mode="HTML",
            )

        # Answer the callback query
        await callback.answer()

    async def handle_consent_callback(
        self, callback: CallbackQuery, user: User, state: FSMContext, **kwargs
    ):
        """Handle consent callbacks."""

        action = callback.data.split(":")[1]

        if action == "accept":
            await self.process_consent_acceptance(callback, user, state)
        elif action == "reject":
            await self.process_consent_rejection(callback, user, state)
        elif action == "read_terms":
            # Just answer the callback, terms are already linked in the message
            await callback.answer(
                "Пожалуйста, ознакомьтесь с соглашениями по ссылкам выше"
            )

    async def process_consent_acceptance(
        self, callback: CallbackQuery, user: User, state: FSMContext
    ):
        """Process consent acceptance."""

        # Get IP address for audit
        ip_address = self.get_user_ip(callback)

        # Process full consent
        result = await self.consent_manager.process_consent_response(
            user.telegram_id, "full_consent", True, ip_address
        )

        if result.success:
            await callback.message.edit_text(
                text=LegalTexts.SUCCESS_MESSAGE,
                reply_markup=OnboardingKeyboards.completion_keyboard(),
                parse_mode="HTML",
            )

            # Set state to COMPLETED
            await state.set_state(OnboardingStates.COMPLETED)

            # Log successful registration
            logger.info(f"User {user.telegram_id} completed onboarding successfully")
        else:
            await callback.message.edit_text(
                text="❌ Произошла ошибка при регистрации. Попробуйте еще раз.",
                reply_markup=OnboardingKeyboards.welcome_keyboard(),
            )

        # Answer the callback query
        await callback.answer()

    async def process_consent_rejection(
        self, callback: CallbackQuery, user: User, state: FSMContext
    ):
        """Process consent rejection."""

        await callback.message.edit_text(
            text=LegalTexts.REJECTION_MESSAGE, parse_mode="HTML"
        )

        # Reset state
        await state.clear()

        # Log rejection
        logger.info(f"User {user.telegram_id} rejected consent during onboarding")

        # Answer the callback query
        await callback.answer()


# Initialize handler and register routes
async def setup_onboarding_handler(user_service: UserService):
    """Setup the onboarding handler with dependencies."""

    # Import here to avoid circular imports
    from app.compliance.age_verification import AgeVerificationService

    # Create services
    age_verification_service = AgeVerificationService(user_service)
    consent_manager = ConsentManager(user_service, age_verification_service)
    onboarding_handler = OnboardingHandler(consent_manager)

    # Register handlers
    onboarding_router.message.register(
        onboarding_handler.handle_start_command, Command("start")
    )

    onboarding_router.callback_query.register(
        onboarding_handler.handle_onboarding_callback,
        lambda c: c.data and c.data.startswith("onboarding:"),
    )

    onboarding_router.callback_query.register(
        onboarding_handler.handle_consent_callback,
        lambda c: c.data and c.data.startswith("consent:"),
    )

    return onboarding_router
