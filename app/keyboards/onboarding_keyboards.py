"""Keyboards for the onboarding and verification process."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class OnboardingKeyboards:
    """Keyboards for the onboarding process."""

    @staticmethod
    def welcome_keyboard() -> InlineKeyboardMarkup:
        """Welcome keyboard for starting registration."""
        keyboard = InlineKeyboardBuilder()
        keyboard.add(
            InlineKeyboardButton(
                text="🚀 Начать регистрацию", callback_data="onboarding:start"
            )
        )
        keyboard.add(
            InlineKeyboardButton(
                text="ℹ️ Подробнее о боте", callback_data="onboarding:info"
            )
        )
        return keyboard.as_markup()

    @staticmethod
    def consent_keyboard() -> InlineKeyboardMarkup:
        """Keyboard for consent agreement."""
        keyboard = InlineKeyboardBuilder()
        keyboard.add(
            InlineKeyboardButton(
                text="✅ Принимаю все условия", callback_data="consent:accept"
            )
        )
        keyboard.add(
            InlineKeyboardButton(text="❌ Не принимаю", callback_data="consent:reject")
        )
        keyboard.add(
            InlineKeyboardButton(
                text="📖 Читать соглашения", callback_data="consent:read_terms"
            )
        )
        keyboard.adjust(1)  # One button per row
        return keyboard.as_markup()

    @staticmethod
    def completion_keyboard() -> InlineKeyboardMarkup:
        """Keyboard after successful registration."""
        keyboard = InlineKeyboardBuilder()
        keyboard.add(
            InlineKeyboardButton(
                text="🎭 Выбрать персонажа", callback_data="main:characters"
            )
        )
        keyboard.add(
            InlineKeyboardButton(text="👤 Мой профиль", callback_data="main:profile")
        )
        return keyboard.as_markup()

    @staticmethod
    def info_keyboard() -> InlineKeyboardMarkup:
        """Keyboard for the bot info screen."""
        keyboard = InlineKeyboardBuilder()
        keyboard.add(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="onboarding:start")
        )
        keyboard.add(
            InlineKeyboardButton(
                text="🚀 Начать регистрацию", callback_data="onboarding:start"
            )
        )
        keyboard.adjust(2)  # Two buttons per row
        return keyboard.as_markup()
