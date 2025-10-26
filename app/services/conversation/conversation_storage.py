"""Модуль для сохранения диалогов пользователей."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.lexicon.gettext import get_log_text
from app.models.conversation import Conversation, ConversationStatus
from app.utils.validators import InputValidator

# if TYPE_CHECKING:
#     from app.services.conversation.conversation_context import UserAIConversationContext


async def save_conversation_to_db(
    session: AsyncSession,
    user_id: int,
    user_message: str,
    ai_response: str,
    ai_model: str,
    tokens_used: int,
    response_time: float,
) -> bool:
    """
    Сохранение диалога в базе данных.

    Args:
        session: Сессия базы данных
        user_id: ID пользователя
        user_message: Сообщение пользователя
        ai_response: Ответ AI
        ai_model: Модель AI
        tokens_used: Количество использованных токенов
        response_time: Время ответа в секундах

    Returns:
        bool: True если успешно сохранено, False в случае ошибки
    """
    try:
        # Валидация входных данных
        is_valid, error_msg = InputValidator.validate_message_length(
            user_message, InputValidator.MAX_MESSAGE_LENGTH
        )
        if not is_valid:
            logger.error(f"Invalid user message: {error_msg}")
            return False

        is_valid, error_msg = InputValidator.validate_message_length(
            ai_response, InputValidator.MAX_RESPONSE_LENGTH
        )
        if not is_valid:
            logger.error(f"Invalid AI response: {error_msg}")
            return False

        # Санитизация текста
        user_message = InputValidator.sanitize_text(user_message)
        ai_response = InputValidator.sanitize_text(ai_response)

        # Валидация числовых параметров
        if tokens_used < 0 or tokens_used > 100000:
            logger.error(f"Invalid tokens_used: {tokens_used}")
            return False

        if response_time < 0 or response_time > 300:  # Максимум 5 минут
            logger.error(f"Invalid response_time: {response_time}")
            return False

        # Создаем запись сообщения пользователя
        user_conv = Conversation(
            user_id=user_id,
            message_text=user_message,
            role="user",
            status=ConversationStatus.COMPLETED,
        )
        session.add(user_conv)

        # Создаем запись ответа AI
        ai_conv = Conversation(
            user_id=user_id,
            message_text=user_message,
            response_text=ai_response,
            role="assistant",
            status=ConversationStatus.COMPLETED,
            ai_model=ai_model,
            tokens_used=tokens_used,
            response_time_ms=int(response_time * 1000),
        )
        session.add(ai_conv)

        await session.commit()
        logger.info(
            get_log_text("message.message_conversation_saved").format(user_id=user_id)
        )
        return True

    except Exception:
        logger.exception(
            get_log_text("message.message_conversation_save_error").format(
                user_id=user_id
            )
        )
        await session.rollback()
        return False


async def save_conversation_context_from_cache(
    cache_service: Any,
    user_id: int,
    user_message: str,
    ai_response: str,
    ai_model: str,
    tokens_used: int,
    response_time: float,
    cache_ttl: int = 600,  # 10 minutes default
) -> bool:
    """
    Сохранение контекста диалога в базе данных только из кэша и после периода неактивности пользователя.

    Args:
        cache_service: Сервис кэширования
        user_id: ID пользователя
        user_message: Сообщение пользователя
        ai_response: Ответ AI
        ai_model: Модель AI
        tokens_used: Количество использованных токенов
        response_time: Время ответа в секундах
        cache_ttl: Время жизни кэша в секундах

    Returns:
        bool: True если успешно сохранено, False в случае ошибки
    """
    try:
        from app.config import get_config
        from app.database import get_session

        config = get_config()

        # Проверяем, включено ли сохранение
        if not config.conversation.enable_saving:
            return True

        # Валидация входных данных
        is_valid, error_msg = InputValidator.validate_message_length(
            user_message, InputValidator.MAX_MESSAGE_LENGTH
        )
        if not is_valid:
            logger.error(f"Invalid user message: {error_msg}")
            return False

        is_valid, error_msg = InputValidator.validate_message_length(
            ai_response, InputValidator.MAX_RESPONSE_LENGTH
        )
        if not is_valid:
            logger.error(f"Invalid AI response: {error_msg}")
            return False

        # Санитизация текста
        user_message = InputValidator.sanitize_text(user_message)
        ai_response = InputValidator.sanitize_text(ai_response)

        # Валидация числовых параметров
        if tokens_used < 0 or tokens_used > 100000:
            logger.error(f"Invalid tokens_used: {tokens_used}")
            return False

        if response_time < 0 or response_time > 300:  # Максимум 5 минут
            logger.error(f"Invalid response_time: {response_time}")
            return False

        # Получаем время последней активности пользователя из кэша
        last_activity = await cache_service.get_user_last_activity(user_id)

        # Если нет данных о последней активности, сохраняем сразу
        if not last_activity:
            async with get_session() as session:
                from app.services.conversation.conversation_storage import (
                    save_conversation_to_db,
                )

                return await save_conversation_to_db(
                    session=session,
                    user_id=user_id,
                    user_message=user_message,
                    ai_response=ai_response,
                    ai_model=ai_model,
                    tokens_used=tokens_used,
                    response_time=response_time,
                )

        # Проверяем, прошло ли достаточно времени с последней активности
        current_time = datetime.now(UTC)
        inactivity_duration = (current_time - last_activity).total_seconds()

        # Если прошло достаточно времени, сохраняем в БД
        if inactivity_duration >= cache_ttl:
            async with get_session() as session:
                from app.services.conversation.conversation_storage import (
                    save_conversation_to_db,
                )

                return await save_conversation_to_db(
                    session=session,
                    user_id=user_id,
                    user_message=user_message,
                    ai_response=ai_response,
                    ai_model=ai_model,
                    tokens_used=tokens_used,
                    response_time=response_time,
                )

        # Если не прошло достаточно времени, просто возвращаем успех
        # Данные остаются в кэше до следующего сохранения
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении контекста диалога из кэша: {e}")
        return False


async def save_all_pending_conversations(cache_service: Any) -> int:
    """
    Сохранение всех ожидающих диалогов из кэша в базу данных.

    Эта функция должна вызываться периодически для сохранения данных,
    которые накопились в кэше, но еще не были сохранены в БД.

    Args:
        cache_service: Сервис кэширования

    Returns:
        int: Количество успешно сохраненных диалогов
    """
    saved_count = 0
    try:
        from app.database import get_session
        from app.services.conversation.conversation_storage import (
            save_conversation_to_db,
        )
        from app.utils.validators import InputValidator

        # Получаем все данные из кэша, которые ожидают сохранения
        # We need to access the memory cache directly
        pending_data = cache_service.memory_cache._conversation_context_cache.copy()

        if not pending_data:
            logger.info("Нет данных для сохранения в БД")
            return saved_count

        logger.info(f"Сохранение {len(pending_data)} записей из кэша в БД")

        # Сохраняем каждую запись
        for user_id, data_entry in pending_data.items():
            # Проверяем, не истекло ли время жизни данных
            if datetime.now(UTC) > data_entry["expires_at"]:
                logger.debug(f"Данные для пользователя {user_id} истекли, пропускаем")
                # Удаляем устаревшие данные из кэша
                await cache_service.memory_cache.delete_pending_conversation_data(
                    user_id
                )
                continue

            data = data_entry["data"]
            try:
                # Валидация входных данных
                is_valid, error_msg = InputValidator.validate_message_length(
                    data["user_message"], InputValidator.MAX_MESSAGE_LENGTH
                )
                if not is_valid:
                    logger.error(
                        f"Invalid user message for user {user_id}: {error_msg}"
                    )
                    continue

                is_valid, error_msg = InputValidator.validate_message_length(
                    data["ai_response"], InputValidator.MAX_RESPONSE_LENGTH
                )
                if not is_valid:
                    logger.error(f"Invalid AI response for user {user_id}: {error_msg}")
                    continue

                # Санитизация текста
                user_message = InputValidator.sanitize_text(data["user_message"])
                ai_response = InputValidator.sanitize_text(data["ai_response"])

                # Валидация числовых параметров
                tokens_used = data["tokens_used"]
                response_time = data["response_time"]

                if tokens_used < 0 or tokens_used > 100000:
                    logger.error(
                        f"Invalid tokens_used for user {user_id}: {tokens_used}"
                    )
                    continue

                if response_time < 0 or response_time > 300:  # Максимум 5 минут
                    logger.error(
                        f"Invalid response_time for user {user_id}: {response_time}"
                    )
                    continue

                async with get_session() as session:
                    result = await save_conversation_to_db(
                        session=session,
                        user_id=user_id,
                        user_message=user_message,
                        ai_response=ai_response,
                        ai_model=data["ai_model"],
                        tokens_used=tokens_used,
                        response_time=response_time,
                    )
                    if result:
                        logger.info(
                            f"Успешно сохранены данные для пользователя {user_id}"
                        )
                        # Удаляем сохраненные данные из кэша
                        await (
                            cache_service.memory_cache.delete_pending_conversation_data(
                                user_id
                            )
                        )
                        saved_count += 1
                    else:
                        logger.error(
                            f"Ошибка при сохранении данных для пользователя {user_id}"
                        )
            except Exception as e:
                logger.error(
                    f"❌ Ошибка при сохранении данных для пользователя {user_id}: {e}"
                )

        logger.info(
            f"Завершено сохранение всех ожидающих диалогов. Сохранено: {saved_count}"
        )

    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении ожидающих диалогов: {e}")

    return saved_count
