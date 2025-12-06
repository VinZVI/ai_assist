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

from app.compliance.consent_manager import ConsentManager, OnboardingState
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
        logger.info(f"Set FSM state to WELCOME for user {user.telegram_id}")

        # Log the current state to verify it was set
        current_state = await state.get_state()
        logger.info(f"Verified FSM state for user {user.telegram_id}: {current_state}")

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

        # Log the callback data for debugging
        logger.info(f"Received onboarding callback with data: {callback.data}")

        # Log current state
        current_state = await state.get_state()
        logger.info(f"Current FSM state: {current_state}")

        # Ensure we have data and it starts with "onboarding:"
        if not callback.data or not callback.data.startswith("onboarding:"):
            logger.warning(f"Invalid onboarding callback data: {callback.data}")
            await callback.answer("Invalid callback data")
            return

        try:
            # Split the callback data to get the action
            parts = callback.data.split(":")
            if len(parts) < 2:
                logger.error(f"Malformed onboarding callback data: {callback.data}")
                await callback.answer("Invalid callback format")
                return

            action = parts[1]
            logger.info(f"Processing onboarding action: {action}")
        except Exception as e:
            logger.error(
                f"Error processing onboarding callback data '{callback.data}': {e}"
            )
            await callback.answer("Error processing callback")
            return

        if action == "start":
            try:
                await callback.message.edit_text(
                    text=LegalTexts.CONSENT_TEXT,
                    reply_markup=OnboardingKeyboards.consent_keyboard(),
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )
                logger.info(f"Updated message for user {user.telegram_id}")

                # Set state to CONSENT
                await state.set_state(OnboardingStates.CONSENT)
                logger.info(f"Set FSM state to CONSENT for user {user.telegram_id}")
            except Exception as e:
                logger.error(f"Error updating message for user {user.telegram_id}: {e}")
                try:
                    await callback.message.answer(
                        text=LegalTexts.CONSENT_TEXT,
                        reply_markup=OnboardingKeyboards.consent_keyboard(),
                        parse_mode="HTML",
                    )
                    await state.set_state(OnboardingStates.CONSENT)
                    logger.info(
                        f"Sent new message and set FSM state to CONSENT for user {user.telegram_id}"
                    )
                except Exception as e2:
                    logger.error(
                        f"Error sending new message for user {user.telegram_id}: {e2}"
                    )
                    # Final fallback - just answer the callback to prevent hanging
                    await callback.answer("Registration process started!")
                    # Set state even if message sending failed
                    await state.set_state(OnboardingStates.CONSENT)
                    logger.info(
                        f"Set FSM state to CONSENT for user {user.telegram_id} despite message errors"
                    )
        elif action == "info":
            try:
                await callback.message.edit_text(
                    text=LegalTexts.BOT_INFO_MESSAGE,
                    reply_markup=OnboardingKeyboards.info_keyboard(),
                    parse_mode="HTML",
                )
                logger.info(f"Updated message with info for user {user.telegram_id}")
            except Exception as e:
                logger.error(
                    f"Error updating message with info for user {user.telegram_id}: {e}"
                )
                # Fallback - just answer the callback to prevent hanging
                await callback.answer(LegalTexts.BOT_INFO_MESSAGE)
        else:
            logger.warning(f"Unknown onboarding action: {action}")
            await callback.answer("Unknown action")

        # Answer the callback query
        await callback.answer()

    async def handle_consent_callback(
        self, callback: CallbackQuery, user: User, state: FSMContext, **kwargs
    ):
        """Handle consent callbacks."""
        
        # Log the callback data for debugging
        logger.info(f"Received consent callback with data: {callback.data}")

        action = callback.data.split(":")[1]
        
        logger.info(f"Processing consent action: {action} for user {user.telegram_id}")

        if action == "accept":
            await self.process_consent_acceptance(callback, user, state)
        elif action == "reject":
            await self.process_consent_rejection(callback, user, state)
        elif action == "read_terms":
            # Just answer the callback, terms are already linked in the message
            await callback.answer(
                "Пожалуйста, ознакомьтесь с соглашениями по ссылкам выше"
            )
        else:
            logger.warning(f"Unknown consent action: {action}")
            await callback.answer("Unknown action")

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

            # Set state based on business logic result
            if result.next_state == OnboardingState.COMPLETED:
                await state.set_state(OnboardingStates.COMPLETED)
                logger.info(
                    f"User {user.telegram_id} completed onboarding successfully"
                )
                # Note: The user object in the handler context may not reflect the updated
                # verification status immediately, but the database has been updated by ConsentManager.
                # The next interaction with this user will fetch the updated user object.
            else:
                # For other states, we might want to handle them differently
                await state.set_state(OnboardingStates.COMPLETED)  # Default fallback
                logger.info(
                    f"User {user.telegram_id} onboarding result: {result.next_state}"
                )
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

    # Register callback handlers
    # Note: We're not using StateFilter here because we want to handle onboarding:start
    # even when the user doesn't have a state set yet (e.g., when they click the button
    # from the AuthMiddleware message)
    onboarding_router.callback_query.register(
        onboarding_handler.handle_onboarding_callback,
        lambda c: c.data and c.data.startswith("onboarding:"),
    )

    # Handle consent callbacks with state filter since these should only be processed
    # when the user is in the CONSENT state
    from aiogram.filters import StateFilter

    onboarding_router.callback_query.register(
        onboarding_handler.handle_consent_callback,
        StateFilter(OnboardingStates.CONSENT),
        lambda c: c.data and c.data.startswith("consent:"),
    )

    return onboarding_router


def get_empty_onboarding_router() -> Router:
    """Get an empty onboarding router for initialization purposes."""
    return Router(name="onboarding")


# Create router for onboarding
onboarding_router = get_empty_onboarding_router()
