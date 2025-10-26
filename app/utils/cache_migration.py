import json
from typing import Any

from loguru import logger

from app.utils.cache_keys import CacheKeyManager


class CacheMigration:
    """Утилиты для миграции ключей кэша."""

    @staticmethod
    async def migrate_conversation_keys(memory_cache: Any, redis_client: Any) -> None:
        """Миграция ключей контекстов диалогов."""
        migrated_count = 0

        # Миграция в memory cache
        old_keys = list(memory_cache._conversation_cache.keys())
        key_manager = CacheKeyManager()

        for old_key in old_keys:
            # Пропускаем уже новые ключи
            if old_key.startswith("conv_ctx:v1:"):
                continue

            try:
                # Парсим старый ключ формата "user_id_limit_max_age_hours"
                if "_" in old_key:
                    parts = old_key.split("_")
                    if len(parts) >= 3 and parts[0].isdigit():
                        user_id = int(parts[0])
                        limit = int(parts[1]) if parts[1].isdigit() else 6
                        max_age_hours = int(parts[2]) if parts[2].isdigit() else 12

                        # Создаем новый ключ
                        new_key = key_manager.conversation_context_key(
                            user_id, limit, max_age_hours
                        )

                        # Переносим данные
                        cached_data = memory_cache._conversation_cache[old_key]
                        memory_cache._conversation_cache[new_key] = cached_data
                        del memory_cache._conversation_cache[old_key]

                        migrated_count += 1
                        logger.debug(f"Migrated cache key: {old_key} -> {new_key}")

            except Exception as e:
                logger.warning(f"Failed to migrate cache key {old_key}: {e}")

        logger.info(f"Migrated {migrated_count} conversation cache keys")

        # Аналогичная миграция для Redis при необходимости
        if redis_client:
            await CacheMigration._migrate_redis_keys(redis_client, key_manager)

    @staticmethod
    async def _migrate_redis_keys(
        redis_client: Any, key_manager: CacheKeyManager
    ) -> None:
        """Миграция ключей Redis."""
        try:
            # Поиск старых ключей
            old_patterns = ["conversation_backup:*", "conversation_context:*"]

            for pattern in old_patterns:
                cursor = 0
                migrated = 0

                while True:
                    cursor, keys = await redis_client.scan(
                        cursor, match=pattern, count=100
                    )

                    for old_key in keys:
                        try:
                            old_key_str = (
                                old_key.decode()
                                if isinstance(old_key, bytes)
                                else old_key
                            )

                            # Пропускаем уже новые ключи
                            if ":v1:" in old_key_str:
                                continue

                            # Получаем данные
                            data = await redis_client.get(old_key)
                            if not data:
                                continue

                            # Генерируем новый ключ в зависимости от типа
                            if old_key_str.startswith("conversation_backup:"):
                                user_id = int(old_key_str.split(":")[1])
                                new_key = key_manager.conversation_backup_key(user_id)
                            elif old_key_str.startswith("conversation_context:"):
                                # Парсинг более сложный, используем параметры по умолчанию
                                user_id = int(old_key_str.split(":")[1])
                                new_key = key_manager.conversation_context_key(user_id)
                            else:
                                continue

                            # Получаем TTL старого ключа
                            ttl = await redis_client.ttl(old_key)
                            if ttl > 0:
                                # Переносим с сохранением TTL
                                await redis_client.setex(new_key, ttl, data)
                            else:
                                # Переносим без TTL
                                await redis_client.set(new_key, data)

                            # Удаляем старый ключ
                            await redis_client.delete(old_key)
                            migrated += 1

                        except Exception as e:
                            logger.warning(
                                f"Failed to migrate Redis key {old_key}: {e}"
                            )

                    if cursor == 0:
                        break

                logger.info(f"Migrated {migrated} Redis keys for pattern {pattern}")

        except Exception as e:
            logger.error(f"Failed to migrate Redis keys: {e}")
