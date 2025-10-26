import asyncio
import json
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

from loguru import logger


class ConversationPersistence:
    """Надежная персистентность контекстов диалогов.

    Обеспечивает надежное сохранение контекста диалогов с тройной защитой:
    1. В памяти для быстрого доступа
    2. В Redis для персистентности между перезапусками
    3. В базу данных для долгосрочного хранения

    Контекст диалога содержит отдельно последние 5 сообщений пользователя
    и 5 ответов ИИ, что позволяет ИИ лучше понимать контекст разговора.
    """

    def __init__(self, redis_client: Any, db_flush_interval: int = 600) -> None:
        """
        Инициализация персистентности контекстов диалогов.

        Args:
            redis_client: Клиент Redis для персистентности
            db_flush_interval: Интервал сброса в базу данных в секундах (по умолчанию 10 минут)
        """
        self.redis = redis_client
        self.memory_buffer: dict[int, dict[str, Any]] = {}
        self.db_flush_interval = db_flush_interval
        self.backup_key_prefix = "conversation_backup"
        self.context_key_prefix = "conversation_context"

        # Запуск фонового процесса сохранения
        self._backup_task = None
        self._shutdown_event = asyncio.Event()

    async def start_background_backup(self) -> None:
        """Запуск фонового процесса периодического бэкапа."""
        self._backup_task = asyncio.create_task(self._background_backup_loop())
        logger.info("Conversation persistence background backup started")

    async def stop_background_backup(self) -> None:
        """Остановка фонового процесса."""
        self._shutdown_event.set()
        if self._backup_task:
            await self._backup_task
        logger.info("Conversation persistence background backup stopped")

    async def save_conversation_context(
        self, user_id: int, context: dict[str, Any], immediate_backup: bool = False
    ) -> None:
        """Сохранение контекста с тройной защитой.

        Контекст диалога содержит отдельно последние 5 сообщений пользователя
        и 5 ответов ИИ, что позволяет ИИ лучше понимать контекст разговора.

        Процесс сохранения:
        1. В память (быстрый доступ)
        2. В Redis (персистентность между перезапусками)
        3. В базу данных (долгосрочное хранение)

        Args:
            user_id: ID пользователя
            context: Контекст диалога для сохранения
            immediate_backup: Немедленный бэкап в Redis
        """
        try:
            timestamp = datetime.now(UTC)

            # 1. Сохранение в память (быстрый доступ)
            self.memory_buffer[user_id] = {
                "data": context,
                "timestamp": timestamp,
                "dirty": True,
                "backup_timestamp": None,
            }

            # 2. Немедленный бэкап в Redis при необходимости
            if immediate_backup or self._should_backup_immediately(user_id):
                await self._backup_to_redis(user_id, context, timestamp)
                self.memory_buffer[user_id]["backup_timestamp"] = timestamp
                self.memory_buffer[user_id]["dirty"] = False

            # 3. Проверка необходимости сброса в БД
            if await self._should_flush_to_db(user_id):
                await self._flush_to_database(user_id)

        except Exception as e:
            logger.error(f"Failed to save conversation context for user {user_id}: {e}")

    async def get_conversation_context(
        self, user_id: int, limit: int = 6, max_age_hours: int = 12
    ) -> dict[str, Any] | None:
        """Получение контекста с fallback на Redis и БД.

        Контекст диалога содержит отдельно последние 5 сообщений пользователя
        и 5 ответов ИИ, что позволяет ИИ лучше понимать контекст разговора.

        Args:
            user_id: ID пользователя
            limit: Лимит сообщений
            max_age_hours: Максимальный возраст сообщений в часах

        Returns:
            dict | None: Контекст диалога или None, если не найден
        """
        # 1. Проверка памяти
        if user_id in self.memory_buffer:
            buffer_entry = self.memory_buffer[user_id]
            age_seconds = (datetime.now(UTC) - buffer_entry["timestamp"]).seconds

            if age_seconds < max_age_hours * 3600:
                logger.debug(f"Context retrieved from memory for user {user_id}")
                return buffer_entry["data"].get("context", buffer_entry["data"])

        # 2. Fallback на Redis
        try:
            from app.utils.cache_keys import CacheKeyManager

            key_manager = CacheKeyManager()
            redis_key = key_manager.conversation_context_key(
                user_id, limit, max_age_hours
            )
            redis_data = await self.redis.get(redis_key)

            if redis_data:
                context = json.loads(redis_data)
                # Восстанавливаем в память
                self.memory_buffer[user_id] = {
                    "data": {"context": context},
                    "timestamp": datetime.now(UTC),
                    "dirty": False,
                    "backup_timestamp": datetime.now(UTC),
                }
                logger.info(f"Context restored from Redis for user {user_id}")
                return context

        except Exception as e:
            logger.warning(f"Failed to restore from Redis for user {user_id}: {e}")

        # 3. Fallback на БД
        try:
            from app.database import get_session
            from app.services.conversation.conversation_history import (
                get_conversation_context_from_db,
            )

            async with get_session() as session:
                context = await get_conversation_context_from_db(
                    session, user_id, limit, max_age_hours
                )

                if context and context.get("message_count", 0) > 0:
                    # Восстанавливаем в память и Redis
                    await self.save_conversation_context(
                        user_id, {"context": context}, immediate_backup=True
                    )
                    logger.info(f"Context restored from database for user {user_id}")
                    return context

        except Exception as e:
            logger.error(f"Failed to restore from database for user {user_id}: {e}")

        return None

    async def _backup_to_redis(
        self, user_id: int, context: dict[str, Any], timestamp: datetime
    ) -> None:
        """Бэкап контекста в Redis."""
        try:
            from app.utils.cache_keys import CacheKeyManager

            key_manager = CacheKeyManager()

            # Основной ключ для восстановления
            backup_key = key_manager.conversation_backup_key(user_id)
            backup_data = {
                "context": context,
                "timestamp": timestamp.isoformat(),
                "version": 1,
            }

            # Сохраняем с TTL = db_flush_interval + запас времени
            await self.redis.setex(
                backup_key,
                self.db_flush_interval + 300,  # +5 минут запас
                json.dumps(backup_data, ensure_ascii=False),
            )

            # Дополнительный ключ для быстрого поиска
            context_key = key_manager.conversation_context_key(
                user_id, 6, 12
            )  # Стандартные параметры
            await self.redis.setex(
                context_key,
                1800,  # 30 минут
                json.dumps(context.get("context", context), ensure_ascii=False),
            )

            logger.debug(f"Context backed up to Redis for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to backup to Redis for user {user_id}: {e}")

    def _should_backup_immediately(self, user_id: int) -> bool:
        """Определяет, нужен ли немедленный бэкап."""
        if user_id not in self.memory_buffer:
            return True

        buffer_entry = self.memory_buffer[user_id]

        # Бэкап если данные грязные и прошло > 60 секунд
        if buffer_entry["dirty"] and buffer_entry.get("backup_timestamp"):
            seconds_since_backup = (
                datetime.now(UTC) - buffer_entry["backup_timestamp"]
            ).seconds
            return seconds_since_backup > 60

        # Бэкап если никогда не делали бэкап
        return buffer_entry.get("backup_timestamp") is None

    async def _should_flush_to_db(self, user_id: int) -> bool:
        """Определяет, нужен ли сброс в БД."""
        if user_id not in self.memory_buffer:
            return False

        buffer_entry = self.memory_buffer[user_id]
        age_seconds = (datetime.now(UTC) - buffer_entry["timestamp"]).seconds

        return age_seconds >= self.db_flush_interval

    async def _flush_to_database(self, user_id: int) -> None:
        """Сброс контекста в базу данных."""
        try:
            if user_id not in self.memory_buffer:
                return

            context_data = self.memory_buffer[user_id]["data"]

            # Извлекаем данные для сохранения
            conv_data = context_data.get("conversation_data", {})
            context = context_data.get("context", {})

            # Сохраняем контекст в Redis для быстрого доступа
            try:
                from app.utils.cache_keys import CacheKeyManager

                key_manager = CacheKeyManager()
                context_key = key_manager.conversation_context_key(user_id, 6, 12)
                await self.redis.setex(
                    context_key,
                    1800,  # 30 минут
                    json.dumps(context, ensure_ascii=False),
                )
            except Exception as e:
                logger.warning(
                    f"Failed to save context to Redis for user {user_id}: {e}"
                )

            # Сохраняем данные разговора в БД
            if conv_data:
                from app.database import get_session
                from app.services.conversation.conversation_storage import (
                    save_conversation_to_db,
                )

                async with get_session() as session:
                    success = await save_conversation_to_db(
                        session=session,
                        user_id=user_id,
                        user_message=conv_data["user_message"],
                        ai_response=conv_data["ai_response"],
                        ai_model=conv_data["ai_model"],
                        tokens_used=conv_data["tokens_used"],
                        response_time=conv_data["response_time"],
                    )

                    if success:
                        # Удаляем из буфера после успешного сохранения
                        del self.memory_buffer[user_id]

                        # Удаляем из Redis
                        from app.utils.cache_keys import CacheKeyManager

                        key_manager = CacheKeyManager()
                        backup_key = key_manager.conversation_backup_key(user_id)
                        await self.redis.delete(backup_key)

                        logger.info(f"Context flushed to database for user {user_id}")
                    else:
                        logger.error(
                            f"Failed to flush context to database for user {user_id}"
                        )

        except Exception as e:
            logger.error(f"Error flushing to database for user {user_id}: {e}")

    async def _background_backup_loop(self) -> None:
        """Фоновый процесс периодического бэкапа."""
        while not self._shutdown_event.is_set():
            try:
                # Бэкап всех грязных контекстов
                for user_id, buffer_entry in list(self.memory_buffer.items()):
                    if buffer_entry["dirty"] or self._should_backup_immediately(
                        user_id
                    ):
                        await self._backup_to_redis(
                            user_id, buffer_entry["data"], buffer_entry["timestamp"]
                        )
                        buffer_entry["backup_timestamp"] = datetime.now(UTC)
                        buffer_entry["dirty"] = False

                # Ожидание следующего цикла (30 секунд)
                try:
                    await asyncio.wait_for(self._shutdown_event.wait(), timeout=30)
                    break  # Если событие установлено, выходим
                except TimeoutError:
                    continue  # Таймаут - продолжаем цикл

            except Exception as e:
                logger.error(f"Error in background backup loop: {e}")
                await asyncio.sleep(30)

    async def restore_all_contexts_on_startup(self) -> int:
        """Восстановление всех контекстов при старте приложения."""
        restored_count = 0

        try:
            # Поиск всех ключей бэкапа
            from app.utils.cache_keys import CacheKeyManager

            key_manager = CacheKeyManager()
            backup_pattern = f"{key_manager.PREFIXES['conversation_backup']}:*"
            backup_keys = []

            # Используем SCAN для больших наборов ключей
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor, match=backup_pattern, count=100
                )
                backup_keys.extend(keys)
                if cursor == 0:
                    break

            logger.info(f"Found {len(backup_keys)} backup keys to restore")

            # Восстановление каждого контекста
            for backup_key in backup_keys:
                try:
                    # Извлекаем user_id из ключа
                    key_str = (
                        backup_key.decode()
                        if isinstance(backup_key, bytes)
                        else backup_key
                    )
                    user_id = int(key_str.split(":")[2])  # conv_backup:v1:user_id

                    # Получаем данные бэкапа
                    backup_data_str = await self.redis.get(backup_key)
                    if not backup_data_str:
                        continue

                    backup_data = json.loads(backup_data_str)
                    context = backup_data["context"]

                    # Восстанавливаем в память
                    self.memory_buffer[user_id] = {
                        "data": {"context": context},
                        "timestamp": datetime.fromisoformat(backup_data["timestamp"]),
                        "dirty": False,
                        "backup_timestamp": datetime.now(UTC),
                    }

                    restored_count += 1

                except Exception as e:
                    logger.warning(f"Failed to restore backup key {backup_key}: {e}")

            logger.info(f"Restored {restored_count} conversation contexts from Redis")

        except Exception as e:
            logger.error(f"Failed to restore contexts on startup: {e}")

        return restored_count
