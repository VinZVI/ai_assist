"""
@file: keyboards/inline.py
@description: Inline клавиатуры для Telegram бота
@dependencies: aiogram
@created: 2025-09-14
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.lexicon.gettext import get_text


def create_main_menu_keyboard(lang_code: str = "ru") -> InlineKeyboardMarkup:
    """Создание основного меню бота."""
    builder = InlineKeyboardBuilder()

    # Кнопки основного меню
    builder.row(
        InlineKeyboardButton(
            text=get_text("keyboards.main_menu_start_chat", lang_code),
            callback_data="start_chat",
        ),
        InlineKeyboardButton(
            text=get_text("keyboards.main_menu_profile", lang_code),
            callback_data="my_stats",
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=get_text("keyboards.main_menu_premium", lang_code),
            callback_data="premium_info",
        ),
        InlineKeyboardButton(
            text=get_text("keyboards.main_menu_help", lang_code), callback_data="help"
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=get_text("keyboards.main_menu_limits", lang_code),
            callback_data="settings",
        ),
    )

    return builder.as_markup()


def create_premium_keyboard(
    premium_price: int = 99, lang_code: str = "ru"
) -> InlineKeyboardMarkup:
    """Создание клавиатуры для премиум функций."""
    builder = InlineKeyboardBuilder()

    # Информация о премиум
    builder.row(
        InlineKeyboardButton(
            text=get_text("keyboards.premium_buy", lang_code, price=premium_price),
            callback_data=f"buy_premium:{premium_price}",
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=get_text("keyboards.premium_features", lang_code),
            callback_data="premium_features",
        ),
        InlineKeyboardButton(
            text=get_text("keyboards.premium_faq", lang_code),
            callback_data="premium_faq",
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=get_text("keyboards.back_to_menu", lang_code),
            callback_data="main_menu",
        ),
    )

    return builder.as_markup()


def create_premium_features_keyboard(lang_code: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура для показа функций премиума."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=get_text("keyboards.buy_premium", lang_code),
            callback_data="premium_info",
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=get_text("keyboards.back", lang_code), callback_data="premium_info"
        ),
        InlineKeyboardButton(
            text=get_text("keyboards.main_menu", lang_code), callback_data="main_menu"
        ),
    )

    return builder.as_markup()


def create_stats_keyboard(lang_code: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура для статистики пользователя."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=get_text("keyboards.detailed_stats", lang_code),
            callback_data="detailed_stats",
        ),
        InlineKeyboardButton(
            text=get_text("keyboards.achievements", lang_code),
            callback_data="achievements",
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=get_text("keyboards.main_menu", lang_code), callback_data="main_menu"
        ),
    )

    return builder.as_markup()


def create_settings_keyboard(lang_code: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура настроек."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=get_text("keyboards.language", lang_code),
            callback_data="settings_language",
        ),
        InlineKeyboardButton(
            text=get_text("keyboards.notifications", lang_code),
            callback_data="settings_notifications",
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=get_text("keyboards.delete_data", lang_code),
            callback_data="settings_delete_data",
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=get_text("keyboards.main_menu", lang_code), callback_data="main_menu"
        ),
    )

    return builder.as_markup()


def create_language_keyboard(lang_code: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура выбора языка."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=get_text("language.available_languages.ru", lang_code),
            callback_data="select_language:ru",
        ),
        InlineKeyboardButton(
            text=get_text("language.available_languages.en", lang_code),
            callback_data="select_language:en",
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=get_text("keyboards.back", lang_code), callback_data="settings"
        ),
    )

    return builder.as_markup()


def create_help_keyboard(lang_code: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура помощи."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=get_text("keyboards.guide", lang_code), callback_data="help_guide"
        ),
        InlineKeyboardButton(
            text=get_text("keyboards.faq", lang_code), callback_data="help_faq"
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=get_text("keyboards.support", lang_code), callback_data="help_support"
        ),
        InlineKeyboardButton(
            text=get_text("keyboards.bug_report", lang_code),
            callback_data="help_bug_report",
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=get_text("keyboards.main_menu", lang_code), callback_data="main_menu"
        ),
    )

    return builder.as_markup()


# Экспорт функций
__all__ = [
    "create_help_keyboard",
    "create_language_keyboard",
    "create_main_menu_keyboard",
    "create_premium_features_keyboard",
    "create_premium_keyboard",
    "create_settings_keyboard",
    "create_stats_keyboard",
]
