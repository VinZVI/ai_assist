"""
@file: services/cache_service.py
@description: Сервис кеширования для пользователей и других данных
@dependencies: asyncio, datetime, typing
@created: 2025-10-15
"""

import asyncio
from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

from loguru import logger

from app.models.user import User
from app.services.conversation_persistence import ConversationPersistence
from app.services.redis_cache_service import RedisCache, get_redis_cache
from app.utils.cache_keys import CacheKeyManager


class MemoryCache:
    """In-memory cache service with TTL support."""

    def __init__(self, ttl_seconds: int = 300, max_size: int = 1000) -> None:
        """
        Инициализация кеша.

        Args:
            ttl_seconds: Время жизни записей в секундах
            max_size: Максимальный размер кеша
        """
        self._cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        self._stats_cache: dict[str, Any] = {}
        self._conversation_cache: dict[str, dict[str, Any]] = {}
        self._conversation_context_cache: dict[
            int, dict[str, Any]
        ] = {}  # Dedicated conversation context cache
        self._user_stats_cache: dict[str, Any] = {}
        self._user_activity_cache: dict[int, datetime] = {}  # Track user activity
        # Store reference to Redis cache
        self.redis_cache: RedisCache | None = None
        # Cache key manager for consistent key generation
        self.key_manager = CacheKeyManager()

    def set_redis_cache(self, redis_cache: RedisCache | None) -> None:
        """Set the Redis cache reference."""
        self.redis_cache = redis_cache

    async def get(self, telegram_id: int) -> User | None:
        """
        Получение значения из кеша.

        Args:
            telegram_id: ID пользователя в Telegram

        Returns:
            User | None: Пользователь или None, если не найден или истек TTL
        """
        # Используем унифицированный ключ
        cache_key = self.key_manager.user_key(telegram_id)

        if cache_key not in self._cache:
            self._misses += 1
            return None

        cached_data = self._cache[cache_key]
        if datetime.now(UTC) > cached_data["expires_at"]:
            # Удаляем устаревшую запись
            del self._cache[cache_key]
            self._misses += 1
            return None

        # Перемещаем запись в конец (для LRU)
        self._cache.move_to_end(cache_key)
        self._hits += 1
        return cached_data["user"]

    async def get_conversation_context(
        self, user_id: int, limit: int = 6, max_age_hours: int = 12
    ) -> dict[str, Any] | None:
        """
        Получение контекста диалога из кеша.

        Args:
            user_id: ID пользователя
            limit: Лимит сообщений
            max_age_hours: Максимальный возраст сообщений в часах

        Returns:
            dict | None: Контекст диалога или None, если не найден или истек TTL
        """
        # Generate cache key consistently with set_conversation_context
        cache_key = self.key_manager.conversation_context_key(
            user_id, limit, max_age_hours
        )

        if cache_key not in self._conversation_cache:
            # Попытка найти с устаревшими ключами (для совместимости)
            legacy_keys = [
                f"{user_id}_{limit}_{max_age_hours}",
                f"{user_id}_6_12",  # Старый формат по умолчанию
            ]

            for legacy_key in legacy_keys:
                if legacy_key in self._conversation_cache:
                    # Мигрируем на новый ключ
                    cached_data = self._conversation_cache[legacy_key]
                    del self._conversation_cache[legacy_key]

                    self._conversation_cache[cache_key] = cached_data
                    logger.info(f"Migrated cache key: {legacy_key} -> {cache_key}")
                    break
            else:
                return None

        cached_data = self._conversation_cache[cache_key]
        if datetime.now(UTC) > cached_data["expires_at"]:
            # Удаляем устаревшую запись
            del self._conversation_cache[cache_key]
            return None

        return cached_data["context"]

    async def get_stats_cache(self) -> dict[str, Any] | None:
        """
        Получение статистики из кеша.

        Returns:
            dict | None: Статистика или None, если не найдена или истек TTL
        """
        if not self._stats_cache:
            return None

        if datetime.now(UTC) > self._stats_cache["expires_at"]:
            # Удаляем устаревшую запись
            self._stats_cache = {}
            return None

        return self._stats_cache["stats"]

    async def get_user_stats(self) -> dict[str, Any] | None:
        """
        Получение статистики пользователей из кеша.

        Returns:
            dict | None: Статистика пользователей или None, если не найдена или истек TTL
        """
        if not self._user_stats_cache:
            return None

        if datetime.now(UTC) > self._user_stats_cache["expires_at"]:
            # Удаляем устаревшую запись
            self._user_stats_cache = {}
            return None

        return self._user_stats_cache["stats"]

    async def set(self, user: User) -> None:
        """
        Сохранение значения в кеше.

        Args:
            user: Пользователь для кеширования
        """
        # Используем унифицированный ключ
        cache_key = self.key_manager.user_key(user.telegram_id)

        # Если кеш переполнен, удаляем самую старую запись
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)

        self._cache[cache_key] = {
            "user": user,
            "expires_at": datetime.now(UTC) + timedelta(seconds=self._ttl),
        }
        # Перемещаем запись в конец (для LRU)
        self._cache.move_to_end(cache_key)

    async def set_conversation_context(
        self,
        user_id: int,
        context: dict[str, Any],
        limit: int = 6,
        max_age_hours: int = 12,
        ttl_seconds: int = 1800,
    ) -> None:
        """
        Сохранение контекста диалога в кеше.

        Args:
            user_id: ID пользователя
            context: Контекст диалога для кеширования
            limit: Лимит сообщений
            max_age_hours: Максимальный возраст сообщений в часах
            ttl_seconds: Время жизни записи в секундах (по умолчанию 30 минут)
        """
        # Используем унифицированный ключ
        cache_key = self.key_manager.conversation_context_key(
            user_id, limit, max_age_hours
        )

        self._conversation_cache[cache_key] = {
            "context": context,
            "expires_at": datetime.now(UTC) + timedelta(seconds=ttl_seconds),
        }

    async def set_conversation_data(
        self, user_id: int, data: dict[str, Any], ttl_seconds: int = 600
    ) -> None:
        """
        Сохранение данных диалога для последующего сохранения в БД.

        Args:
            user_id: ID пользователя
            data: Данные диалога для сохранения
            ttl_seconds: Время жизни записи в секундах (должно соответствовать времени неактивности)
        """
        self._conversation_context_cache[user_id] = {
            "data": data,
            "expires_at": datetime.now(UTC) + timedelta(seconds=ttl_seconds),
        }

    async def get_conversation_data(self, user_id: int) -> dict[str, Any] | None:
        """
        Получение данных диалога для сохранения в БД.

        Args:
            user_id: ID пользователя

        Returns:
            dict | None: Данные диалога или None, если не найдены или истек TTL
        """
        if user_id not in self._conversation_context_cache:
            return None

        cached_data = self._conversation_context_cache[user_id]
        if datetime.now(UTC) > cached_data["expires_at"]:
            # Удаляем устаревшую запись
            del self._conversation_context_cache[user_id]
            return None

        return cached_data["data"]

    async def set_stats_cache(
        self, stats: dict[str, Any], ttl_seconds: int = 300
    ) -> None:
        """
        Сохранение статистики в кеше.

        Args:
            stats: Статистика для кеширования
            ttl_seconds: Время жизни записи в секундах
        """
        self._stats_cache = {
            "stats": stats,
            "expires_at": datetime.now(UTC) + timedelta(seconds=ttl_seconds),
        }

    async def set_user_stats(
        self, stats: dict[str, Any], ttl_seconds: int = 300
    ) -> None:
        """
        Сохранение статистики пользователей в кеше.

        Args:
            stats: Статистика для кеширования
            ttl_seconds: Время жизни записи в секундах
        """
        self._user_stats_cache = {
            "stats": stats,
            "expires_at": datetime.now(UTC) + timedelta(seconds=ttl_seconds),
        }

    async def delete(self, telegram_id: int) -> None:
        """
        Удаление значения из кеша.

        Args:
            telegram_id: ID пользователя в Telegram
        """
        # Используем унифицированный ключ
        cache_key = self.key_manager.user_key(telegram_id)
        if cache_key in self._cache:
            del self._cache[cache_key]

    async def delete_conversation_context(self, user_id: int) -> None:
        """
        Удаление контекста диалога из кеша.

        Args:
            user_id: ID пользователя
        """
        # Удаляем все ключи пользователя (новые и старые форматы)
        keys_to_delete = []

        # Поиск по новому формату
        for key in self._conversation_cache:
            parsed = self.key_manager.parse_key(key)
            if (
                parsed["valid"]
                and parsed["prefix"] == CacheKeyManager.PREFIXES["conversation_context"]
                and len(parsed["components"]) >= 3
                and int(parsed["components"][2]) == user_id
            ):  # user_id is third component after prefix:version:
                keys_to_delete.append(key)

        # Поиск по старому формату (для совместимости)
        for key in self._conversation_cache:
            if key.startswith(f"{user_id}_"):
                keys_to_delete.append(key)

        # Удаление найденных ключей
        for key in keys_to_delete:
            del self._conversation_cache[key]

        # Удаляем данные для сохранения в БД
        if user_id in self._conversation_context_cache:
            del self._conversation_context_cache[user_id]

    async def delete_pending_conversation_data(self, user_id: int) -> None:
        """
        Удаление данных ожидающего диалога из кеша.

        Args:
            user_id: ID пользователя
        """
        # Удаляем только данные для сохранения в БД
        if user_id in self._conversation_context_cache:
            del self._conversation_context_cache[user_id]

    async def set_user_activity(self, user_id: int) -> None:
        """
        Сохранение времени последней активности пользователя.

        Args:
            user_id: ID пользователя
        """
        self._user_activity_cache[user_id] = datetime.now(UTC)

    async def get_user_last_activity(self, user_id: int) -> datetime | None:
        """
        Получение времени последней активности пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            datetime | None: Время последней активности или None
        """
        return self._user_activity_cache.get(user_id)

    async def delete_user_activity(self, user_id: int) -> None:
        """
        Удаление записи о последней активности пользователя.

        Args:
            user_id: ID пользователя
        """
        if user_id in self._user_activity_cache:
            del self._user_activity_cache[user_id]

    def get_stats(self) -> dict[str, Any]:
        """
        Получение статистики кэширования.

        Returns:
            dict: Статистика кэширования
        """
        stats: dict[str, Any] = {
            "total_requests": self._hits + self._misses,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / (self._hits + self._misses)
            if (self._hits + self._misses) > 0
            else 0,
            "cache_size": len(self._cache),
            "max_size": self._max_size,
            "conversation_cache_size": len(self._conversation_cache),
        }

        # Добавляем статистику Redis кэша, если он инициализирован
        if self.redis_cache:
            stats["redis_cache"] = self.redis_cache.get_stats()
        else:
            stats["redis_cache"] = {"status": "not_initialized"}

        return stats

    def reset_stats(self) -> None:
        """Сброс статистики кеша."""
        self._hits = 0
        self._misses = 0
        self._user_activity_cache.clear()  # Clear user activity cache on reset


class CacheService:
    """Сервис кеширования с поддержкой нескольких уровней."""

    def __init__(self, memory_ttl: int = 300, memory_max_size: int = 1000) -> None:
        """
        Инициализация сервиса кеширования.

        Args:
            memory_ttl: Время жизни записей в памяти в секундах
            memory_max_size: Максимальный размер кеша в памяти
        """
        self.memory_cache = MemoryCache(memory_ttl, memory_max_size)
        self.redis_cache: RedisCache | None = None
        self.conversation_persistence: ConversationPersistence | None = None
        self._lock = asyncio.Lock()

    async def initialize_redis_cache(self) -> None:
        """Инициализация Redis кеша и персистентности."""
        try:
            self.redis_cache = await get_redis_cache()
            if self.redis_cache:
                await self.redis_cache.initialize()
                logger.info("Redis cache initialized in CacheService")
            else:
                # If get_redis_cache returns None, create a new instance
                from app.services.redis_cache_service import initialize_redis_cache

                self.redis_cache = await initialize_redis_cache()
                if self.redis_cache:
                    await self.redis_cache.initialize()
                    logger.info(
                        "Redis cache initialized in CacheService (new instance)"
                    )

            # Set the Redis cache reference in MemoryCache
            self.memory_cache.set_redis_cache(self.redis_cache)

            # Инициализация персистентности контекстов
            if self.redis_cache:
                self.conversation_persistence = ConversationPersistence(
                    self.redis_cache.redis_client, db_flush_interval=600
                )

                # Восстановление контекстов при старте
                restored = await self.conversation_persistence.restore_all_contexts_on_startup()
                logger.info(f"Restored {restored} conversations from Redis backup")

                # Запуск фонового процесса
                await self.conversation_persistence.start_background_backup()
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache in CacheService: {e}")
            self.redis_cache = None

    async def get_user(self, telegram_id: int) -> User | None:
        """
        Получение пользователя из кеша.

        Args:
            telegram_id: ID пользователя в Telegram

        Returns:
            User | None: Пользователь или None, если не найден
        """
        # Сначала проверяем memory cache
        user = await self.memory_cache.get(telegram_id)
        if user:
            return user

        # Если нет в memory cache, проверяем Redis cache
        if self.redis_cache:
            user = await self.redis_cache.get_user(telegram_id)
            if user:
                # Кешируем в memory cache для будущих запросов
                await self.memory_cache.set(user)
                return user

        return None

    async def get_conversation_context(
        self, user_id: int, limit: int = 6, max_age_hours: int = 12
    ) -> dict[str, Any] | None:
        """
        Получение контекста диалога из кеша.

        Args:
            user_id: ID пользователя
            limit: Лимит сообщений
            max_age_hours: Максимальный возраст сообщений в часах

        Returns:
            dict | None: Контекст диалога или None, если не найден
        """
        # Используем персистентность контекстов если доступна
        if self.conversation_persistence:
            context = await self.conversation_persistence.get_conversation_context(
                user_id, limit, max_age_hours
            )
            if context:
                return context

        # Сначала проверяем memory cache
        context = await self.memory_cache.get_conversation_context(
            user_id, limit, max_age_hours
        )
        if context:
            return context

        # Если нет в memory cache, проверяем Redis cache
        if self.redis_cache:
            # Для простоты предполагаем, что контекст хранится в Redis как специальный ключ
            # В реальной реализации может потребоваться отдельная логика
            pass

        return None

    async def get_user_stats(self) -> dict[str, Any] | None:
        """
        Получение статистики пользователей из кеша.

        Returns:
            dict | None: Статистика пользователей или None, если не найдена
        """
        # Сначала проверяем memory cache
        stats = await self.memory_cache.get_user_stats()
        if stats:
            return stats

        # Если нет в memory cache, проверяем Redis cache
        if self.redis_cache:
            # Для простоты предполагаем, что статистика хранится в Redis как специальный ключ
            # В реальной реализации может потребоваться отдельная логика
            pass

        return None

    async def set_user(self, user: User) -> None:
        """
        Сохранение пользователя в кеше.

        Args:
            user: Пользователь для кеширования
        """
        # Сохраняем в memory cache
        await self.memory_cache.set(user)

        # Сохраняем в Redis cache
        if self.redis_cache:
            await self.redis_cache.set(user)

    async def set_conversation_context(
        self,
        user_id: int,
        context: dict[str, Any],
        limit: int = 6,
        max_age_hours: int = 12,
        ttl_seconds: int = 1800,
    ) -> None:
        """
        Сохранение контекста диалога в кеше.

        Args:
            user_id: ID пользователя
            context: Контекст диалога для кеширования
            limit: Лимит сообщений
            max_age_hours: Максимальный возраст сообщений в часах
            ttl_seconds: Время жизни записи в секундах
        """
        # Используем персистентность контекстов если доступна
        if self.conversation_persistence:
            await self.conversation_persistence.save_conversation_context(
                user_id,
                {"conversation_data": context},
                immediate_backup=False,  # Будет сохранено в фоне
            )
        else:
            # Сохраняем в memory cache
            await self.memory_cache.set_conversation_context(
                user_id, context, limit, max_age_hours, ttl_seconds
            )

        # Сохраняем в Redis cache (если реализовано)
        if self.redis_cache:
            # В реальной реализации может потребоваться отдельная логика
            pass

    async def set_conversation_data(
        self, user_id: int, data: dict[str, Any], ttl_seconds: int = 600
    ) -> None:
        """
        Сохранение данных диалога для последующего сохранения в БД.

        Args:
            user_id: ID пользователя
            data: Данные диалога для сохранения
            ttl_seconds: Время жизни записи в секундах (должно соответствовать времени неактивности)
        """
        # Сохраняем в memory cache
        await self.memory_cache.set_conversation_data(user_id, data, ttl_seconds)

        # Сохраняем в Redis cache (если реализовано)
        if self.redis_cache:
            # В реальной реализации может потребоваться отдельная логика
            pass

    async def get_conversation_data(self, user_id: int) -> dict[str, Any] | None:
        """
        Получение данных диалога для сохранения в БД.

        Args:
            user_id: ID пользователя

        Returns:
            dict | None: Данные диалога или None, если не найдены
        """
        # Сначала проверяем memory cache
        data = await self.memory_cache.get_conversation_data(user_id)
        if data:
            return data

        # Если нет в memory cache, проверяем Redis cache
        if self.redis_cache:
            # Для простоты предполагаем, что контекст хранится в Redis как специальный ключ
            # В реальной реализации может потребоваться отдельная логика
            pass

        return None

    async def set_user_stats(
        self, stats: dict[str, Any], ttl_seconds: int = 300
    ) -> None:
        """
        Сохранение статистики пользователей в кеше.

        Args:
            stats: Статистика для кеширования
            ttl_seconds: Время жизни записи в секундах
        """
        # Сохраняем в memory cache
        await self.memory_cache.set_user_stats(stats, ttl_seconds)

        # Сохраняем в Redis cache (если реализовано)
        if self.redis_cache:
            # В реальной реализации может потребоваться отдельная логика
            pass

    async def delete_user(self, telegram_id: int) -> None:
        """
        Удаление пользователя из кеша.

        Args:
            telegram_id: ID пользователя в Telegram
        """
        # Удаляем из memory cache
        await self.memory_cache.delete(telegram_id)

        # Удаляем из Redis cache
        if self.redis_cache:
            await self.redis_cache.delete(telegram_id)

    async def delete_conversation_context(self, user_id: int) -> None:
        """
        Удаление контекста диалога из кеша.

        Args:
            user_id: ID пользователя
        """
        # Удаляем из memory cache
        await self.memory_cache.delete_conversation_context(user_id)

        # Удаляем из Redis cache (если реализовано)
        if self.redis_cache:
            # В реальной реализации может потребоваться отдельная логика
            pass

    async def set_user_activity(self, user_id: int) -> None:
        """
        Сохранение времени последней активности пользователя.

        Args:
            user_id: ID пользователя
        """
        # Сохраняем в memory cache
        await self.memory_cache.set_user_activity(user_id)

        # Сохраняем в Redis cache (если реализовано)
        if self.redis_cache:
            # В реальной реализации может потребоваться отдельная логика
            pass

    async def get_user_last_activity(self, user_id: int) -> datetime | None:
        """
        Получение времени последней активности пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            datetime | None: Время последней активности или None
        """
        # Сначала проверяем memory cache
        last_activity = await self.memory_cache.get_user_last_activity(user_id)
        if last_activity:
            return last_activity

        # Если нет в memory cache, проверяем Redis cache
        if self.redis_cache:
            # Для простоты предполагаем, что контекст хранится в Redis как специальный ключ
            # В реальной реализации может потребоваться отдельная логика
            pass

        return None

    async def delete_user_activity(self, user_id: int) -> None:
        """
        Удаление записи о последней активности пользователя.

        Args:
            user_id: ID пользователя
        """
        # Удаляем из memory cache
        await self.memory_cache.delete_user_activity(user_id)

        # Удаляем из Redis cache (если реализовано)
        if self.redis_cache:
            # В реальной реализации может потребоваться отдельная логика
            pass

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Получение статистики кеша.

        Returns:
            dict: Статистика кеша
        """
        stats = {"memory_cache": self.memory_cache.get_stats()}

        if self.redis_cache:
            stats["redis_cache"] = self.redis_cache.get_stats()
        else:
            stats["redis_cache"] = {"status": "not_initialized"}

        return stats

    def reset_cache_stats(self) -> None:
        """Сброс статистики кеша."""
        self.memory_cache.reset_stats()
        if self.redis_cache:
            self.redis_cache.reset_stats()

    async def shutdown(self) -> None:
        """Корректное завершение работы сервиса кеширования."""
        if self.conversation_persistence:
            await self.conversation_persistence.stop_background_backup()


# Глобальный экземпляр сервиса кеширования
cache_service = CacheService()


__all__ = [
    "CacheService",
    "cache_service",
]
