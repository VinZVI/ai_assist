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
from app.lexicon.gettext import get_log_text, get_text
from app.models import User, UserCreate

# Создаем роутер для обработчиков команды start
start_router = Router(name="start")


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
    lang_code = user.language_code or "ru"

    # Базовое приветствие
    welcome_text = f"""
🤖 <b>{get_text("start.welcome_title", lang_code, display_name=display_name)}</b>

{get_text("start.welcome_intro", lang_code)}

<b>{get_text("start.functionality_title", lang_code)}</b>
"""
    for item in get_text("start.functionality_items", lang_code):
        welcome_text += f"• {item}\n"

    welcome_text += f"""
<b>{get_text("start.limits_title", lang_code)}</b>
• {get_text("start.limits_free", lang_code, free_limit=config.user_limits.free_messages_limit)}
• {get_text("start.limits_used", lang_code, used=user.daily_message_count, total=config.user_limits.free_messages_limit)}
"""

    # Дополнительная информация для премиум пользователей
    if user.is_premium_active():
        welcome_text += f"\n{get_text('start.premium_active', lang_code)}"
    else:
        welcome_text += f"""
<b>{get_text("start.premium_info_title", lang_code)}</b>
{
            get_text(
                "start.premium_info",
                lang_code,
                price=config.user_limits.premium_price,
                days=config.user_limits.premium_duration_days,
            )
        }
"""

    welcome_text += f"\n\n{get_text('start.commands_info', lang_code)}"

    return welcome_text


@start_router.message(CommandStart())
async def handle_start_command(message: Message, user: User) -> None:
    """
    Обработчик команды /start.

    Отправляет приветственное сообщение с информацией о боте.
    Пользователь уже аутентифицирован через middleware.

    Args:
        message: Объект сообщения от пользователя
        user: Объект пользователя из middleware
    """
    try:
        # Получаем конфигурацию
        config = get_config()

        # Логируем попытку старта
        logger.info(
            get_log_text("start.start_command_received").format(user_id=user.id)
        )

        # Обновляем информацию о пользователе если что-то изменилось
        # ВАЖНО: Не обновляем language_code, чтобы сохранить выбор пользователя
        user_updated = False

        if (
            message.from_user
            and hasattr(message.from_user, "username")
            and user.username != message.from_user.username
        ):
            user.username = message.from_user.username
            user_updated = True

        if (
            message.from_user
            and hasattr(message.from_user, "first_name")
            and user.first_name != message.from_user.first_name
        ):
            user.first_name = message.from_user.first_name
            user_updated = True

        if (
            message.from_user
            and hasattr(message.from_user, "last_name")
            and user.last_name != message.from_user.last_name
        ):
            user.last_name = message.from_user.last_name
            user_updated = True

        # Обновляем время последней активности
        user.last_activity_at = datetime.now(UTC)
        user.updated_at = datetime.now(UTC)

        # Сбрасываем дневной счетчик если прошел день
        user.reset_daily_count_if_needed()

        if user_updated:
            async with get_session() as session:
                session.add(user)
                await session.commit()
                logger.info(
                    get_log_text("start.start_user_info_updated").format(
                        user_id=user.id
                    )
                )

        # Формируем приветственное сообщение
        welcome_message = format_welcome_message(user, config)

        # Отправляем приветственное сообщение с клавиатурой
        sent_message = await message.answer(
            welcome_message,
            reply_markup=create_main_menu_keyboard(user.language_code or "ru"),
            parse_mode="HTML",
        )

        logger.info(
            get_log_text("start.start_command_processed").format(
                user_id=user.id,
                message_id=sent_message.message_id,
            )
        )

    except Exception as e:
        logger.error(
            get_log_text("start.start_unexpected_error").format(
                user_id=user.id, error=e
            )
        )
        try:
            await message.answer(
                get_text("errors.general_error", user.language_code or "ru")
            )
        except Exception as send_error:
            logger.error(
                get_log_text("start.start_error_sending_message").format(
                    error=send_error,
                )
            )
