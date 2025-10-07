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
from app.lexicon.gettext import get_text
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
        new_text = get_text("callbacks.main_menu_title")
        new_keyboard = create_main_menu_keyboard()

        # Only edit if message exists and content/markup are different
        if callback.message:
            if (
                callback.message.text != new_text
                or callback.message.reply_markup != new_keyboard
            ):
                await callback.message.edit_text(
                    new_text,
                    reply_markup=new_keyboard,
                    parse_mode="Markdown",
                )
            else:
                # Message content is the same, just answer the callback
                await callback.answer()
        else:
            # If there's no message, send a new one
            await callback.message.answer(
                new_text,
                reply_markup=new_keyboard,
                parse_mode="Markdown",
            )
            await callback.answer()
    except Exception as e:
        # Handle the specific "message is not modified" error
        if "message is not modified" in str(e).lower():
            # Just answer the callback without doing anything
            await callback.answer()
        else:
            logger.error(CALLBACK_MAIN_MENU_ERROR.format(error=e))
            # Try to send a new message if editing fails
            try:
                await callback.message.answer(
                    get_text("callbacks.main_menu_title"),
                    reply_markup=create_main_menu_keyboard(),
                    parse_mode="Markdown",
                )
                await callback.answer()
            except Exception as fallback_error:
                logger.error(
                    CALLBACK_MAIN_MENU_FALLBACK_ERROR.format(error=fallback_error)
                )
                await callback.answer(get_text("errors.general_error"))


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
    await callback.answer(get_text("callbacks.placeholder_message"))


# Экспорт роутера
__all__ = ["callback_router"]
