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
                # ВАЖНО: Не обновляем language_code, чтобы сохранить выбор пользователя
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

                # Обновляем время последней активности
                existing_user.last_activity_at = datetime.now(UTC)
                existing_user.updated_at = datetime.now(UTC)

                # Сбрасываем дневной счетчик если прошел день
                existing_user.reset_daily_count_if_needed()

                if user_updated:
                    await session.commit()
                    logger.info(
                        get_log_text("start.start_user_info_updated").format(
                            user_id=telegram_user.id
                        )
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
                get_log_text("start.start_user_created").format(
                    user_id=telegram_user.id, username=telegram_user.username
                )
            )
            return new_user

        except IntegrityError as e:
            await session.rollback()
            logger.error(
                get_log_text("start.start_user_creation_error").format(
                    user_id=telegram_user.id, error=e
                )
            )
            return None

        except Exception as e:
            await session.rollback()
            logger.error(
                get_log_text("start.start_unexpected_error").format(
                    user_id=telegram_user.id, error=e
                )
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
        logger.info(
            get_log_text("start.start_command_received").format(
                user_id=message.from_user.id
            )
        )

        # Получаем или создаем пользователя
        user = await get_or_create_user(message.from_user)
        if not user:
            logger.error(
                get_log_text("start.start_command_error").format(
                    user_id=message.from_user.id
                )
            )
            await message.answer(get_text("errors.user_registration_error"))
            return

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
                user_id=message.from_user.id,
                message_id=sent_message.message_id,
            )
        )

    except Exception as e:
        logger.error(
            get_log_text("start.start_unexpected_error").format(
                user_id=message.from_user.id, error=e
            )
        )
        try:
            await message.answer(get_text("errors.general_error"))
        except Exception as send_error:
            logger.error(
                get_log_text("start.start_error_sending_message").format(
                    error=send_error,
                )
            )
