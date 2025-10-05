"""
@file: callbacks.py
@description: Обработчики callback-запросов для Telegram бота
@dependencies: aiogram, sqlalchemy, loguru
@created: 2025-09-12
"""

from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery
from loguru import logger
from sqlalchemy import select

from app.config import get_config
from app.database import get_session
from app.keyboards import create_main_menu_keyboard
from app.lexicon.callbacks import (
    MAIN_MENU_ERROR,
    MAIN_MENU_FALLBACK_ERROR,
    MAIN_MENU_TEXT,
    PLACEHOLDER_MESSAGE,
)
from app.log_lexicon.callbacks import (
    CALLBACK_MAIN_MENU_ERROR,
    CALLBACK_MAIN_MENU_FALLBACK_ERROR,
)
from app.models import User

# Создаем роутер для обработчиков callback-запросов
callback_router = Router(name="callbacks")


@callback_router.callback_query()
async def show_main_menu(callback: CallbackQuery) -> None:
    """Показать главное меню."""
    try:
        # Check if the message content and reply markup are actually different
        # before attempting to edit to prevent "message is not modified" error
        new_text = MAIN_MENU_TEXT
        new_keyboard = create_main_menu_keyboard()

        if (
            callback.message.text != new_text
            or callback.message.reply_markup != new_keyboard
        ):
            await callback.message.edit_text(
                new_text,
                reply_markup=new_keyboard,
                parse_mode="Markdown",
            )
        await callback.answer()
    except Exception as e:
        logger.error(CALLBACK_MAIN_MENU_ERROR.format(error=e))
        # Try to send a new message if editing fails
        try:
            await callback.message.answer(
                MAIN_MENU_TEXT,
                reply_markup=create_main_menu_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer()
        except Exception as fallback_error:
            logger.error(CALLBACK_MAIN_MENU_FALLBACK_ERROR.format(error=fallback_error))
            await callback.answer(MAIN_MENU_ERROR)


# Заглушки для остальных callback'ов
@callback_router.callback_query(
    F.data.in_(
        [
            "detailed_stats",
            "achievements",
            "settings_notifications",
            "settings_delete_data",
            "lang_ru",
            "lang_en",
            "help_guide",
            "help_faq",
            "help_support",
            "help_bug_report",
            "premium_faq",
            "other_payment_methods",
        ],
    ),
)
async def placeholder_callback(callback: CallbackQuery) -> None:
    """Заглушка для еще не реализованных функций."""
    await callback.answer(PLACEHOLDER_MESSAGE)


# Экспорт роутера
__all__ = ["callback_router"]
