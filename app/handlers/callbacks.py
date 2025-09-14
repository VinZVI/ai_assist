"""
@file: handlers/callbacks.py
@description: Обработчики callback запросов от inline клавиатур
@dependencies: aiogram, sqlalchemy
@created: 2025-09-14
"""

from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from loguru import logger

from app.config import get_config
from app.database import get_session
from app.keyboards import (
    create_back_button,
    create_help_keyboard,
    create_language_keyboard,
    create_main_menu_keyboard,
    create_payment_keyboard,
    create_premium_features_keyboard,
    create_premium_keyboard,
    create_settings_keyboard,
    create_stats_keyboard,
)
from app.models import User

# Создаем роутер для callback запросов
callback_router = Router()


@callback_router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery) -> None:
    """Показать главное меню."""
    try:
        await callback.message.edit_text(
            "🏠 **Главное меню**\n\n"
            "Выберите действие:",
            reply_markup=create_main_menu_keyboard(),
            parse_mode="Markdown",
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"❌ Ошибка при показе главного меню: {e}")
        await callback.answer("Произошла ошибка. Попробуйте еще раз.")


@callback_router.callback_query(F.data == "start_chat")
async def start_chat(callback: CallbackQuery) -> None:
    """Начать диалог с ботом."""
    try:
        await callback.message.edit_text(
            "💬 **Начинаем диалог!**\n\n"
            "Теперь просто напишите мне сообщение, и я отвечу вам. "
            "Я готов выслушать вас и оказать эмоциональную поддержку.\n\n"
            "✨ *Что вас беспокоит или о чём хотели бы поговорить?*",
            reply_markup=create_back_button("main_menu"),
            parse_mode="Markdown",
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"❌ Ошибка при начале диалога: {e}")
        await callback.answer("Произошла ошибка. Попробуйте еще раз.")


@callback_router.callback_query(F.data == "my_stats")
async def show_my_stats(callback: CallbackQuery) -> None:
    """Показать статистику пользователя."""
    try:
        if not callback.from_user:
            await callback.answer("Не удалось получить данные пользователя.")
            return

        async with get_session() as session:
            from sqlalchemy import select
            
            # Получаем пользователя
            stmt = select(User).where(User.telegram_id == callback.from_user.id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                await callback.answer("Пользователь не найден. Используйте /start для регистрации.")
                return

            # Формируем статистику
            premium_status = "💎 Активен" if user.is_premium_active() else "❌ Неактивен"
            
            stats_text = (
                f"📊 **Ваша статистика**\n\n"
                f"👤 **Пользователь:** {user.get_display_name()}\n"
                f"🗓️ **Зарегистрирован:** {user.created_at.strftime('%d.%m.%Y')}\n"
                f"💎 **Премиум статус:** {premium_status}\n\n"
                f"📈 **Использование:**\n"
                f"💬 Сообщений сегодня: {user.daily_message_count}\n"
                f"📊 Всего сообщений: {user.total_messages}\n"
                f"📅 Последняя активность: {user.last_activity_at.strftime('%d.%m.%Y %H:%M') if user.last_activity_at else 'Неизвестно'}\n"
            )

            await callback.message.edit_text(
                stats_text,
                reply_markup=create_stats_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка при показе статистики: {e}")
        await callback.answer("Произошла ошибка при загрузке статистики.")


@callback_router.callback_query(F.data == "premium_info")
async def show_premium_info(callback: CallbackQuery) -> None:
    """Показать информацию о премиуме."""
    try:
        config = get_config()
        premium_price = config.user_limits.premium_price if config.user_limits else 99
        free_limit = config.user_limits.free_messages_limit if config.user_limits else 10

        premium_text = (
            f"💎 **Премиум доступ**\n\n"
            f"🆓 **Бесплатный план:**\n"
            f"• {free_limit} сообщений в день\n"
            f"• Базовая поддержка ИИ\n\n"
            f"💎 **Премиум план ({premium_price}₽):**\n"
            f"• ♾️ Безлимитные сообщения\n"
            f"• 🚀 Приоритетная обработка\n"
            f"• 🎯 Расширенные возможности ИИ\n"
            f"• 💬 Приоритетная поддержка\n"
            f"• 🔒 Повышенная конфиденциальность\n\n"
            f"⏰ **Длительность:** 30 дней\n"
            f"💳 **Оплата:** Telegram Stars"
        )

        await callback.message.edit_text(
            premium_text,
            reply_markup=create_premium_keyboard(premium_price),
            parse_mode="Markdown",
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка при показе информации о премиуме: {e}")
        await callback.answer("Произошла ошибка. Попробуйте еще раз.")


@callback_router.callback_query(F.data.startswith("buy_premium:"))
async def buy_premium(callback: CallbackQuery) -> None:
    """Купить премиум доступ."""
    try:
        premium_price = int(callback.data.split(":")[1])
        
        payment_text = (
            f"💳 **Оплата премиум доступа**\n\n"
            f"💰 **Стоимость:** {premium_price} Telegram Stars\n"
            f"⏰ **Длительность:** 30 дней\n\n"
            f"🔐 **Что вы получите:**\n"
            f"• Безлимитные сообщения\n"
            f"• Приоритетная обработка\n"
            f"• Расширенные возможности\n\n"
            f"👇 Выберите способ оплаты:"
        )

        await callback.message.edit_text(
            payment_text,
            reply_markup=create_payment_keyboard(premium_price),
            parse_mode="Markdown",
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка при покупке премиума: {e}")
        await callback.answer("Произошла ошибка. Попробуйте еще раз.")


@callback_router.callback_query(F.data == "premium_features")
async def show_premium_features(callback: CallbackQuery) -> None:
    """Показать подробности премиум функций."""
    try:
        features_text = (
            "💎 **Подробности о премиум функциях**\n\n"
            "🚀 **Безлимитные сообщения:**\n"
            "• Отправляйте сколько угодно сообщений в день\n"
            "• Нет ограничений по времени и количеству\n\n"
            "⚡ **Приоритетная обработка:**\n"
            "• Ваши запросы обрабатываются быстрее\n"
            "• Минимальная задержка ответов\n\n"
            "🧠 **Расширенные возможности ИИ:**\n"
            "• Более детальные и вдумчивые ответы\n"
            "• Улучшенная память контекста\n"
            "• Специальные режимы общения\n\n"
            "💬 **Приоритетная поддержка:**\n"
            "• Быстрые ответы от службы поддержки\n"
            "• Индивидуальная помощь\n\n"
            "🔒 **Повышенная конфиденциальность:**\n"
            "• Дополнительная защита данных\n"
            "• Приоритет в обработке запросов"
        )

        await callback.message.edit_text(
            features_text,
            reply_markup=create_premium_features_keyboard(),
            parse_mode="Markdown",
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка при показе функций премиума: {e}")
        await callback.answer("Произошла ошибка. Попробуйте еще раз.")


@callback_router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery) -> None:
    """Показать помощь."""
    try:
        help_text = (
            "ℹ️ **Справка и помощь**\n\n"
            "🤖 **О боте:**\n"
            "Я - ваш AI-компаньон для эмоциональной поддержки. "
            "Моя задача - выслушать вас, понять ваши чувства и оказать поддержку.\n\n"
            "💬 **Как пользоваться:**\n"
            "• Просто напишите мне любое сообщение\n"
            "• Расскажите о своих переживаниях\n"
            "• Задавайте вопросы или просите совета\n\n"
            "🔒 **Конфиденциальность:**\n"
            "• Все диалоги защищены\n"
            "• Данные не передаются третьим лицам\n"
            "• Вы можете удалить историю в любой момент"
        )

        await callback.message.edit_text(
            help_text,
            reply_markup=create_help_keyboard(),
            parse_mode="Markdown",
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка при показе помощи: {e}")
        await callback.answer("Произошла ошибка. Попробуйте еще раз.")


@callback_router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery) -> None:
    """Показать настройки."""
    try:
        settings_text = (
            "⚙️ **Настройки**\n\n"
            "Здесь вы можете настроить работу бота под себя:"
        )

        await callback.message.edit_text(
            settings_text,
            reply_markup=create_settings_keyboard(),
            parse_mode="Markdown",
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка при показе настроек: {e}")
        await callback.answer("Произошла ошибка. Попробуйте еще раз.")


@callback_router.callback_query(F.data == "settings_language")
async def show_language_settings(callback: CallbackQuery) -> None:
    """Показать настройки языка."""
    try:
        language_text = (
            "🌍 **Настройки языка**\n\n"
            "Выберите предпочитаемый язык интерфейса:"
        )

        await callback.message.edit_text(
            language_text,
            reply_markup=create_language_keyboard(),
            parse_mode="Markdown",
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка при показе настроек языка: {e}")
        await callback.answer("Произошла ошибка. Попробуйте еще раз.")


# Заглушки для остальных callback'ов
@callback_router.callback_query(F.data.in_([
    "detailed_stats", "achievements", "settings_notifications", 
    "settings_delete_data", "lang_ru", "lang_en", "help_guide", 
    "help_faq", "help_support", "help_bug_report", "premium_faq",
    "other_payment_methods"
]))
async def placeholder_callback(callback: CallbackQuery) -> None:
    """Заглушка для еще не реализованных функций."""
    await callback.answer("🚧 Эта функция в разработке. Скоро будет доступна!")


@callback_router.callback_query(F.data.startswith("pay_stars:"))
async def pay_with_stars(callback: CallbackQuery) -> None:
    """Оплата через Telegram Stars (заглушка)."""
    try:
        premium_price = int(callback.data.split(":")[1])
        
        # В реальной версии здесь будет интеграция с Telegram Payments API
        await callback.answer(
            f"🚧 Оплата через Telegram Stars ({premium_price} ⭐) в разработке. "
            "Скоро будет доступна!",
            show_alert=True
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка при оплате: {e}")
        await callback.answer("Произошла ошибка при оплате.")


# Экспорт роутера
__all__ = ["callback_router"]