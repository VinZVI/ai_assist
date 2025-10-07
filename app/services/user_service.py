from datetime import UTC, datetime
from typing import TYPE_CHECKING

from aiogram.types import Message
from loguru import logger
from sqlalchemy import select

from app.database import get_session
from app.lexicon.gettext import get_log_text
from app.models.user import User


async def get_or_update_user(message: Message) -> User | None:
    """Получение или создание пользователя на основе сообщения Telegram.

    Args:
        message: Сообщение от пользователя Telegram

    Returns:
        User объект или None в случае ошибки
    """
    if not message.from_user:
        logger.warning("Получено сообщение без информации о пользователе")
        return None

    try:
        async with get_session() as session:
            # Проверяем существование пользователя
            stmt = select(User).where(User.telegram_id == message.from_user.id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                # Обновляем информацию о пользователе, но НЕ обновляем language_code
                user.username = message.from_user.username
                user.first_name = message.from_user.first_name
                user.last_name = message.from_user.last_name
                user.last_activity_at = datetime.now(UTC)

                # Сброс дневного счетчика если прошел день
                if user.reset_daily_count_if_needed():
                    user.daily_message_count = 0
                    user.last_message_date = datetime.now(UTC).date()
            else:
                # Создаем нового пользователя
                user = User(
                    telegram_id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name,
                    language_code=message.from_user.language_code or "ru",
                    last_activity_at=datetime.now(UTC),
                    last_message_date=datetime.now(UTC).date(),
                )
                session.add(user)

            await session.commit()
            await session.refresh(user)

            logger.info(
                f"👤 Пользователь {'обновлен' if user.id else 'создан'}: {user.get_display_name()}"
            )
            return user

    except Exception as e:
        logger.exception("Ошибка при получении/создании пользователя", exc_info=e)
        return None
