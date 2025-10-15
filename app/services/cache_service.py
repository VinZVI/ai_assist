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
from app.services.redis_cache_service import RedisCache, get_redis_cache


class MemoryCache:
    """In-memory cache service with TTL support."""

    def __init__(self, ttl_seconds: int = 300, max_size: int = 1000) -> None:
        """
        Инициализация кеша.

        Args:
            ttl_seconds: Время жизни записей в секундах
            max_size: Максимальный размер кеша
        """
        self._cache: OrderedDict[int, dict[str, Any]] = OrderedDict()
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    async def get(self, key: int) -> User | None:
        """
        Получение значения из кеша.

        Args:
            key: Ключ для поиска

        Returns:
            User | None: Пользователь или None, если не найден или истек TTL
        """
        if key not in self._cache:
            self._misses += 1
            return None

        cached_data = self._cache[key]
        if datetime.now(UTC) > cached_data["expires_at"]:
            # Удаляем устаревшую запись
            del self._cache[key]
            self._misses += 1
            return None

        # Перемещаем запись в конец (для LRU)
        self._cache.move_to_end(key)
        self._hits += 1
        return cached_data["user"]

    async def set(self, user: User) -> None:
        """
        Сохранение значения в кеше.

        Args:
            user: Пользователь для кеширования
        """
        # Если кеш переполнен, удаляем самую старую запись
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)

        self._cache[user.telegram_id] = {
            "user": user,
            "expires_at": datetime.now(UTC) + timedelta(seconds=self._ttl),
        }
        # Перемещаем запись в конец (для LRU)
        self._cache.move_to_end(user.telegram_id)

    async def delete(self, key: int) -> None:
        """
        Удаление значения из кеша.

        Args:
            key: Ключ для удаления
        """
        if key in self._cache:
            del self._cache[key]

    def get_stats(self) -> dict[str, int | float]:
        """
        Получение статистики кеша.

        Returns:
            dict: Статистика кеша
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2),
            "current_size": len(self._cache),
            "max_size": self._max_size,
        }

    def reset_stats(self) -> None:
        """Сброс статистики кеша."""
        self._hits = 0
        self._misses = 0


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
        self._lock = asyncio.Lock()

    async def initialize_redis_cache(self) -> None:
        """Инициализация Redis кеша."""
        try:
            self.redis_cache = await get_redis_cache()
            if self.redis_cache:
                await self.redis_cache.initialize()
                logger.info("Redis cache initialized in CacheService")
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

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Получение статистики кеша.

        Returns:
            dict: Статистика кеша
        """
        stats = {"memory_cache": self.memory_cache.get_stats()}

        if self.redis_cache:
            stats["redis_cache"] = self.redis_cache.get_stats()  # type: ignore
        else:
            stats["redis_cache"] = {"status": "not_initialized"}  # type: ignore

        return stats

    def reset_cache_stats(self) -> None:
        """Сброс статистики кеша."""
        self.memory_cache.reset_stats()
        if self.redis_cache:
            self.redis_cache.reset_stats()


# Глобальный экземпляр сервиса кеширования
cache_service = CacheService()


__all__ = [
    "CacheService",
    "cache_service",
]
