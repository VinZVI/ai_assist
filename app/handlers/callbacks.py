"""
@file: callbacks.py
@description: Обработчики callback-запросов для Telegram бота
@dependencies: aiogram, sqlalchemy, loguru
@created: 2025-09-12
@updated: 2025-10-09
"""

from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, InaccessibleMessage
from loguru import logger
from sqlalchemy import select

from app.config import get_config
from app.database import get_session
from app.keyboards import (
    create_main_menu_keyboard,
    create_premium_keyboard,
    create_settings_keyboard,
    create_stats_keyboard,
)
from app.lexicon.gettext import get_log_text, get_text
from app.models import User

# Создаем роутер для обработчиков callback-запросов
callback_router = Router(name="callbacks")


@callback_router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery, user: User) -> None:
    """Показать главное меню."""
    # Get user's language preference
    user_lang = user.language_code or "ru"

    try:
        # Check if the message content and reply markup are actually different
        # before attempting to edit to prevent "message is not modified" error
        new_text = get_text("callbacks.main_menu_title", user_lang)
        new_keyboard = create_main_menu_keyboard(user_lang)

        # Only edit if message exists and content/markup are different
        if callback.message and not isinstance(callback.message, InaccessibleMessage):
            # Safe to access text attribute now
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
            # If there's no message or it's inaccessible, just answer the callback
            await callback.answer()
    except Exception as e:
        # Handle the specific "message is not modified" error
        if "message is not modified" in str(e).lower():
            # Just answer the callback without doing anything
            await callback.answer()
        else:
            logger.error(
                get_log_text("callbacks.callback_main_menu_error").format(error=e)
            )
            # Try to send a new message if editing fails
            try:
                if callback.message and not isinstance(
                    callback.message, InaccessibleMessage
                ):
                    await callback.message.answer(
                        get_text("callbacks.main_menu_title", user_lang),
                        reply_markup=create_main_menu_keyboard(user_lang),
                        parse_mode="Markdown",
                    )
                await callback.answer()
            except Exception as fallback_error:
                logger.error(
                    get_log_text("callbacks.callback_main_menu_fallback_error").format(
                        error=fallback_error
                    )
                )
                await callback.answer(get_text("errors.general_error", user_lang))


@callback_router.callback_query(F.data == "start_chat")
async def start_chat(callback: CallbackQuery, user: User) -> None:
    """Начать диалог."""
    # Get user's language preference
    user_lang = user.language_code or "ru"

    try:
        # Send a welcome message to start the chat
        if callback.message and not isinstance(callback.message, InaccessibleMessage):
            await callback.message.answer(
                get_text("start.first_message_text", user_lang),
                parse_mode="Markdown",
            )
        await callback.answer()
    except Exception as e:
        logger.error(
            get_log_text("callbacks.callback_error").format(user_id=user.id, error=e)
        )
        await callback.answer(get_text("errors.general_error", user_lang))


@callback_router.callback_query(F.data == "my_stats")
async def show_user_stats(callback: CallbackQuery, user: User) -> None:
    """Показать статистику пользователя."""
    # Get user's language preference
    user_lang = user.language_code or "ru"

    try:
        from app.keyboards import create_stats_keyboard

        # Create a simple stats message
        stats_text = f"📊 *{get_text('profile.title', user_lang)}*\n\n"
        stats_text += f"ID: {user.id}\n"
        stats_text += f"{get_text('limits.total_messages', user_lang, count=user.total_messages)}\n"

        new_keyboard = create_stats_keyboard(user_lang)

        if callback.message and not isinstance(callback.message, InaccessibleMessage):
            await callback.message.edit_text(
                stats_text,
                reply_markup=new_keyboard,
                parse_mode="Markdown",
            )
        else:
            await callback.answer()
    except Exception as e:
        logger.error(
            get_log_text("callbacks.callback_error").format(user_id=user.id, error=e)
        )
        await callback.answer(get_text("errors.general_error", user_lang))


@callback_router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery, user: User) -> None:
    """Показать помощь."""
    # Get user's language preference
    user_lang = user.language_code or "ru"

    try:
        from app.keyboards import create_help_keyboard

        # Create help text
        help_text = f"*{get_text('help.title', user_lang)}*\n\n"
        # Fix: get_text("help.commands", user_lang) returns a list of tuples, not a string
        commands = get_text("help.commands", user_lang)
        if isinstance(commands, list):
            for command, description in commands:
                help_text += f"• `{command}` - {description}\n"
        else:
            # Fallback in case the format changes
            help_text += str(commands)

        new_keyboard = create_help_keyboard(user_lang)

        if callback.message and not isinstance(callback.message, InaccessibleMessage):
            await callback.message.edit_text(
                help_text,
                reply_markup=new_keyboard,
                parse_mode="Markdown",
            )
        else:
            await callback.answer()
    except Exception as e:
        logger.error(
            get_log_text("callbacks.callback_error").format(user_id=user.id, error=e)
        )
        await callback.answer(get_text("errors.general_error", user_lang))


# Заглушки для остальных callback'ов
@callback_router.callback_query(
    F.data.in_(
        [
            "detailed_stats",
            "achievements",
            "settings_notifications",
            "settings_delete_data",
            "help_guide",
            "help_faq",
            "help_support",
            "help_bug_report",
            "premium_faq",
            "other_payment_methods",
        ],
    ),
)
async def placeholder_callback(callback: CallbackQuery, user: User) -> None:
    """Заглушка для еще не реализованных функций."""
    user_lang = user.language_code or "ru"
    await callback.answer(get_text("callbacks.placeholder_message", user_lang))


@callback_router.callback_query(F.data == "settings")
async def show_settings_menu(callback: CallbackQuery, user: User) -> None:
    """Показать меню настроек."""
    # Get user's language preference
    user_lang = user.language_code or "ru"

    try:
        from app.keyboards import create_settings_keyboard

        new_text = get_text("callbacks.settings_menu_title", user_lang)
        new_keyboard = create_settings_keyboard(user_lang)

        if callback.message and not isinstance(callback.message, InaccessibleMessage):
            await callback.message.edit_text(
                new_text,
                reply_markup=new_keyboard,
                parse_mode="Markdown",
            )
        else:
            await callback.answer()
    except Exception as e:
        logger.error(
            get_log_text("callbacks.callback_error").format(user_id=user.id, error=e)
        )
        await callback.answer(get_text("errors.general_error", user_lang))


@callback_router.callback_query(F.data == "settings_language")
async def show_language_settings(callback: CallbackQuery, user: User) -> None:
    """Показать настройки языка."""
    # Get user's language preference
    user_lang = user.language_code or "ru"

    try:
        from app.keyboards import create_language_keyboard

        new_text = get_text("language.title", user_lang)
        new_keyboard = create_language_keyboard(user_lang)

        if callback.message and not isinstance(callback.message, InaccessibleMessage):
            await callback.message.edit_text(
                new_text,
                reply_markup=new_keyboard,
                parse_mode="Markdown",
            )
        else:
            await callback.answer()
    except Exception as e:
        logger.error(
            get_log_text("callbacks.callback_error").format(user_id=user.id, error=e)
        )
        await callback.answer(get_text("errors.general_error", user_lang))


@callback_router.callback_query(F.data == "premium_info")
async def show_premium_info(callback: CallbackQuery, user: User) -> None:
    """Показать информацию о премиуме."""
    # Get user's language preference
    user_lang = user.language_code or "ru"

    try:
        from app.keyboards import create_premium_keyboard

        config = get_config()

        new_text = get_text("callbacks.premium_info_title", user_lang)
        new_keyboard = create_premium_keyboard(
            config.user_limits.premium_price, user_lang
        )

        if callback.message and not isinstance(callback.message, InaccessibleMessage):
            await callback.message.edit_text(
                new_text,
                reply_markup=new_keyboard,
                parse_mode="Markdown",
            )
        else:
            await callback.answer()
    except Exception as e:
        logger.error(
            get_log_text("callbacks.callback_error").format(user_id=user.id, error=e)
        )
        await callback.answer(get_text("errors.general_error", user_lang))


@callback_router.callback_query(F.data.startswith("buy_premium:"))
async def handle_premium_purchase(callback: CallbackQuery, user: User) -> None:
    """Обработать покупку премиум-доступа через Telegram Stars."""
    # Get user's language preference
    user_lang = user.language_code or "ru"

    try:
        # Extract premium price from callback data
        try:
            # Check if callback.data exists before accessing split
            premium_price = (
                int(callback.data.split(":")[1]) if callback.data else 99
            )  # Default price
        except (IndexError, ValueError):
            premium_price = 99  # Default price

        # Get configuration
        config = get_config()

        # Calculate duration based on price (simplified pricing model)
        # In a real implementation, you might have a mapping of prices to durations
        if premium_price >= 800:  # Yearly plan
            duration_days = 365
            description = get_text("premium.description_yearly", user_lang)
        elif premium_price >= 250:  # 3-month plan
            duration_days = 90
            description = get_text("premium.description_quarterly", user_lang)
        else:  # Monthly plan
            duration_days = 30
            description = get_text("premium.description_monthly", user_lang)

        # Create invoice using payment service
        from aiogram import Bot

        from app.services.payment_service import TelegramStarsPaymentService

        bot = Bot(token=config.telegram.bot_token)
        payment_service = TelegramStarsPaymentService(bot)

        success = await payment_service.create_invoice(
            user_id=callback.from_user.id,
            amount=premium_price,
            description=description,
            duration_days=duration_days,
        )

        if not success:
            await callback.answer(
                get_text("errors.payment_creation_failed", user_lang), show_alert=True
            )

    except Exception as e:
        logger.error(
            get_log_text("callbacks.callback_error").format(user_id=user.id, error=e)
        )
        await callback.answer(get_text("errors.general_error", user_lang))


# Экспорт роутера
__all__ = ["callback_router"]
