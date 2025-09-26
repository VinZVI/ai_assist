"""
@file: keyboards/__init__.py
@description: Клавиатуры для Telegram бота
@dependencies: aiogram
@created: 2025-09-07
@updated: 2025-09-14
"""

from .inline import (
    create_back_button,
    create_confirmation_keyboard,
    create_help_keyboard,
    create_language_keyboard,
    create_main_menu_keyboard,
    create_payment_keyboard,
    create_premium_features_keyboard,
    create_premium_keyboard,
    create_settings_keyboard,
    create_stats_keyboard,
)

__all__ = [
    "create_back_button",
    "create_confirmation_keyboard",
    "create_help_keyboard",
    "create_language_keyboard",
    "create_main_menu_keyboard",
    "create_payment_keyboard",
    "create_premium_features_keyboard",
    "create_premium_keyboard",
    "create_settings_keyboard",
    "create_stats_keyboard",
]
