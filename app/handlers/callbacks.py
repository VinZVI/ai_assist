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
from app.models import User

# Создаем роутер для обработчиков callback-запросов
callback_router = Router(name="callbacks")


@callback_router.callback_query()
async def show_main_menu(callback: CallbackQuery) -> None:
    """Показать главное меню."""
    try:
        await callback.message.edit_text(
            "🏠 **Главное меню**\n\nВыберите действие:",
            reply_markup=create_main_menu_keyboard(),
            parse_mode="Markdown",
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"❌ Ошибка при показе главного меню: {e}")
        await callback.answer("Произошла ошибка. Попробуйте еще раз.")


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
    await callback.answer("🚧 Эта функция в разработке. Скоро будет доступна!")


# Экспорт роутера
__all__ = ["callback_router"]
