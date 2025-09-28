"""
@file: handlers/start.py
@description: Обработчик команды /start с регистрацией пользователя
@dependencies: aiogram, sqlalchemy
@created: 2025-09-12
"""

from datetime import UTC, datetime, timezone

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.types import User as TgUser
from loguru import logger
from sqlalchemy.exc import IntegrityError

from app.config import AppConfig, get_config
from app.database import get_session
from app.keyboards import create_main_menu_keyboard
from app.models import User, UserCreate

# Создаем роутер для обработчиков команды start
start_router = Router(name="start")


async def get_or_create_user(telegram_user: TgUser) -> User | None:
    """
    Получение существующего пользователя или создание нового.

    Args:
        telegram_user: Объект пользователя Telegram

    Returns:
        User: Объект пользователя из базы данных
    """
    async with get_session() as session:
        try:
            from sqlalchemy import select

            # Попытка найти существующего пользователя
            stmt = select(User).where(User.telegram_id == telegram_user.id)
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                # Обновляем информацию о пользователе если что-то изменилось
                user_updated = False

                if existing_user.username != telegram_user.username:
                    existing_user.username = telegram_user.username
                    user_updated = True

                if existing_user.first_name != telegram_user.first_name:
                    existing_user.first_name = telegram_user.first_name
                    user_updated = True

                if existing_user.last_name != telegram_user.last_name:
                    existing_user.last_name = telegram_user.last_name
                    user_updated = True

                if existing_user.language_code != telegram_user.language_code:
                    existing_user.language_code = telegram_user.language_code
                    user_updated = True

                # Обновляем время последней активности
                existing_user.last_activity_at = datetime.now(UTC)
                existing_user.updated_at = datetime.now(UTC)

                # Сбрасываем дневной счетчик если прошел день
                existing_user.reset_daily_count_if_needed()

                if user_updated:
                    await session.commit()
                    logger.info(
                        f"👤 Обновлена информация пользователя {telegram_user.id}",
                    )

                return existing_user

            # Создаем нового пользователя
            new_user_data = UserCreate(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code or "ru",
            )

            new_user = User(
                telegram_id=new_user_data.telegram_id,
                username=new_user_data.username,
                first_name=new_user_data.first_name,
                last_name=new_user_data.last_name,
                language_code=new_user_data.language_code,
                last_activity_at=datetime.now(UTC),
            )

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            logger.info(
                f"🆕 Создан новый пользователь: {telegram_user.id} "
                f"(@{telegram_user.username})",
            )
            return new_user

        except IntegrityError as e:
            await session.rollback()
            logger.error(
                f"❌ Ошибка целостности при создании пользователя "
                f"{telegram_user.id}: {e}",
            )
            return None

        except Exception as e:
            await session.rollback()
            logger.error(
                f"💥 Неожиданная ошибка при работе с пользователем "
                f"{telegram_user.id}: {e}",
            )
            return None


def format_welcome_message(user: User, config: AppConfig) -> str:
    """
    Формирование приветственного сообщения для пользователя.

    Args:
        user: Объект пользователя
        config: Конфигурация приложения

    Returns:
        str: Отформатированное приветственное сообщение
    """
    display_name = user.get_display_name()

    # Базовое приветствие
    welcome_text = f"""
🤖 <b>Добро пожаловать в AI-Компаньон, {display_name}!</b>

Я ваш персональный помощник для эмоциональной поддержки и дружеского общения.
Готов выслушать, поддержать и помочь советом в любое время! 💙

<b>🎯 Что я умею:</b>
• Поддерживающие беседы и эмоциональная помощь
• Советы по саморазвитию и мотивация
• Ответы на вопросы и интересные диалоги
• Помощь в решении повседневных задач

<b>📊 Ваши лимиты:</b>
• Бесплатно: <b>{config.user_limits.free_messages_limit} сообщений в день</b>
• Сегодня использовано: <b>{user.daily_message_count}/"
                f"{config.user_limits.free_messages_limit}</b>
"""

    # Дополнительная информация для премиум пользователей
    if user.is_premium_active():
        welcome_text += (
            "\n⭐ <b>У вас активна премиум подписка!</b>\n• Безлимитное "
            "общение без ограничений"
        )
    else:
        welcome_text += f"""
💎 <b>Хотите больше?</b>
• Премиум доступ: <b>{config.user_limits.premium_price} Telegram Stars</b>
• Безлимитное общение на {config.user_limits.premium_duration_days} дней
• Приоритетная поддержка
"""

    welcome_text += """\n\n<i>Команды: /help - справка, /profile - ваш профиль, """
    welcome_text += """/limits - лимиты, /premium - премиум</i>"""

    return welcome_text


@start_router.message(CommandStart())
async def handle_start_command(message: Message) -> None:
    """
    Обработчик команды /start.

    Регистрирует нового пользователя или обновляет информацию существующего,
    отправляет приветственное сообщение с информацией о боте.

    Args:
        message: Объект сообщения от пользователя
    """
    try:
        # Получаем конфигурацию
        config = get_config()

        # Логируем попытку старта
        user_info = (
            f"@{message.from_user.username}"
            if message.from_user.username
            else f"ID:{message.from_user.id}"
        )
        logger.info(f"🚀 Команда /start от пользователя {user_info}")

        # Получаем или создаем пользователя в БД
        user = await get_or_create_user(message.from_user)

        if user is None:
            # Если не удалось создать/получить пользователя
            await message.answer(
                "❌ <b>Произошла ошибка при регистрации</b>\n\n"
                "Попробуйте повторить команду /start через несколько секунд.\n"
                "Если проблема повторяется, обратитесь к администратору.",
                parse_mode="HTML",
            )
            return

        # Формируем и отправляем приветственное сообщение
        welcome_message = format_welcome_message(user, config)

        await message.answer(
            welcome_message,
            parse_mode="HTML",
            reply_markup=create_main_menu_keyboard(),
            disable_web_page_preview=True,
        )

        # Дополнительное сообщение для новых пользователей
        if user.total_messages == 0:
            await message.answer(
                "✨ <b>Это ваше первое сообщение!</b>\n\n"
                "Напишите мне что-нибудь, и я отвечу вам. "
                "Например, расскажите о своем настроении или задайте вопрос! 😊",
                parse_mode="HTML",
            )

        logger.info(
            f"✅ Успешно обработана команда /start для пользователя "
            f"{message.from_user.id}",
        )

    except Exception as e:
        logger.error(
            f"💥 Ошибка в обработчике /start для пользователя "
            f"{message.from_user.id}: {e}",
        )

        # Отправляем пользователю сообщение об ошибке
        try:
            await message.answer(
                "😔 <b>Произошла неожиданная ошибка</b>\n\n"
                "Мы уже работаем над исправлением. "
                "Пожалуйста, попробуйте позже или обратитесь к администратору.",
                parse_mode="HTML",
            )
        except Exception as send_error:
            logger.error(f"💥 Не удалось отправить сообщение об ошибке: {send_error}")


# Экспорт роутера для регистрации в основном приложении
__all__ = ["start_router"]
