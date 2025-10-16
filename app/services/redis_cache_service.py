"""
@file: services/redis_cache_service.py
@description: Redis cache service for persistent user caching
@dependencies: redis, json, app.models.user
@created: 2025-10-15
"""

import asyncio
import json
from datetime import UTC, date, datetime
from typing import Any, Optional

from loguru import logger

from app.config import get_config
from app.models.user import User

# Try to import redis, but handle if it's not available
try:
    import redis

    # Use getattr to access asyncio module to avoid Pyright warnings
    redis_asyncio = getattr(redis, "asyncio", None)
    if redis_asyncio is not None:
        redis_client_module = redis_asyncio
        REDIS_AVAILABLE = True
    else:
        redis_client_module = None
        REDIS_AVAILABLE = False
        logger.warning("Redis asyncio not available, Redis cache will be disabled")
except ImportError:
    redis_client_module = None
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, Redis cache will be disabled")


def serialize_datetime(dt: datetime | None) -> str | None:
    """Serialize datetime object to ISO format string."""
    return dt.isoformat() if dt else None


def deserialize_datetime(dt_str: str | None) -> datetime | None:
    """Deserialize ISO format string to datetime object."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except ValueError:
        return None


def deserialize_date(date_str: str | None) -> date | None:
    """Deserialize ISO format string to date object."""
    if not date_str:
        return None
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        return None


class RedisCache:
    """Redis cache service with TTL support."""

    def __init__(self, redis_url: str | None = None, ttl: int = 3600) -> None:
        """
        Инициализация Redis кеша.

        Args:
            redis_url: URL для подключения к Redis
            ttl: Время жизни записей в секундах
        """
        if not REDIS_AVAILABLE:
            self.redis_client = None
            return

        config = get_config()
        # Use a default Redis URL or check if it exists in config
        self.redis_url = redis_url or getattr(
            config.cache, "redis_url", "redis://localhost:6379"
        )
        self.ttl = ttl
        self.redis_client: Any | None = None  # Using Any to avoid type issues
        self._lock = asyncio.Lock()
        # Stats tracking
        self._hits = 0
        self._misses = 0

    async def initialize(self) -> None:
        """Инициализация подключения к Redis."""
        if not REDIS_AVAILABLE or not self.redis_url or redis_client_module is None:
            self.redis_client = None
            return

        try:
            # Try to connect with the full URL first (with username/password)
            self.redis_client = redis_client_module.from_url(self.redis_url)
            # Проверяем подключение
            if self.redis_client is not None:
                await self.redis_client.ping()
            logger.info(f"Redis cache initialized with URL: {self.redis_url}")
        except Exception as e:
            # If that fails, try to connect with just the password (simple auth)
            try:
                config = get_config()
                if config.cache.redis_password:
                    password_url = f"redis://:{config.cache.redis_password}@{config.cache.redis_host}:{config.cache.redis_port}"
                    self.redis_client = redis_client_module.from_url(password_url)
                    if self.redis_client is not None:
                        await self.redis_client.ping()
                    logger.info(
                        f"Redis cache initialized with password-only URL: {password_url}"
                    )
                else:
                    raise
            except Exception:
                logger.error(f"Failed to initialize Redis cache: {e}")
                self.redis_client = None

    async def get_user(self, telegram_id: int) -> User | None:
        """
        Получение пользователя из Redis кеша.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Объект пользователя или None если не найден
        """
        if not REDIS_AVAILABLE or not self.redis_client:
            return None

        try:
            user_data_str = await self.redis_client.get(f"user:{telegram_id}")
            if user_data_str:
                self._hits += 1
                user_data = json.loads(user_data_str)
                # Создаем и возвращаем объект User из данных
                return User(
                    id=int(user_data.get("id")),
                    telegram_id=int(user_data.get("telegram_id")),
                    username=user_data.get("username"),
                    first_name=user_data.get("first_name"),
                    last_name=user_data.get("last_name"),
                    language_code=user_data.get("language_code"),
                    is_premium=user_data.get("is_premium", False),
                    daily_message_count=int(user_data.get("daily_message_count", 0)),
                    last_message_date=deserialize_date(
                        user_data.get("last_message_date")
                    ),
                    created_at=deserialize_datetime(user_data.get("created_at")),
                    updated_at=deserialize_datetime(user_data.get("updated_at")),
                )
            self._misses += 1
        except Exception as e:
            self._misses += 1
            logger.error(f"Error getting user from Redis cache: {e}")
        return None

    async def set(self, user: User) -> None:
        """
        Сохранение пользователя в Redis кеше.

        Args:
            user: Пользователь для кеширования
        """
        if not REDIS_AVAILABLE or not self.redis_client:
            return

        try:
            # Подготавливаем данные пользователя для сериализации
            user_data = {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "language_code": user.language_code,
                "is_premium": user.is_premium,
                "is_active": user.is_active,
                "is_blocked": user.is_blocked,
                "daily_message_count": user.daily_message_count,
                "total_messages": user.total_messages,
                "last_message_date": user.last_message_date.isoformat()
                if user.last_message_date
                else None,
                "created_at": serialize_datetime(user.created_at),
                "updated_at": serialize_datetime(user.updated_at),
            }

            await self.redis_client.setex(
                f"user:{user.telegram_id}", self.ttl, json.dumps(user_data, default=str)
            )
        except Exception as e:
            logger.error(f"Error setting user to Redis cache: {e}")

    async def delete(self, telegram_id: int) -> None:
        """
        Удаление пользователя из Redis кеша.

        Args:
            telegram_id: ID пользователя в Telegram
        """
        if not REDIS_AVAILABLE or not self.redis_client:
            return

        try:
            await self.redis_client.delete(f"user:{telegram_id}")
        except Exception as e:
            logger.error(f"Error deleting user from Redis cache: {e}")

    async def close(self) -> None:
        """Закрытие подключения к Redis."""
        if REDIS_AVAILABLE and self.redis_client:
            await self.redis_client.close()
            logger.info("Redis cache connection closed")

    def get_stats(self) -> dict[str, Any]:
        """
        Получение статистики Redis кеша.

        Returns:
            dict: Статистика кеша
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2),
            "status": "available"
            if REDIS_AVAILABLE and self.redis_client
            else "not_available",
        }

    def reset_stats(self) -> None:
        """Сброс статистики кеша."""
        self._hits = 0
        self._misses = 0


# Глобальный экземпляр Redis кеша
redis_cache: RedisCache | None = None
_redis_cache_task: asyncio.Task | None = None


async def initialize_redis_cache() -> RedisCache:
    """Инициализация глобального экземпляра Redis кеша."""
    global redis_cache, _redis_cache_task
    if redis_cache is None:
        redis_cache = RedisCache()
        _redis_cache_task = asyncio.create_task(redis_cache.initialize())
    return redis_cache


async def get_redis_cache() -> RedisCache | None:
    """Получение глобального экземпляра Redis кеша."""
    return redis_cache


async def close_redis_cache() -> None:
    """Закрытие глобального экземпляра Redis кеша."""
    global redis_cache, _redis_cache_task
    if redis_cache:
        await redis_cache.close()
        redis_cache = None
    if _redis_cache_task:
        _redis_cache_task.cancel()
        import contextlib

        with contextlib.suppress(asyncio.CancelledError):
            await _redis_cache_task
        _redis_cache_task = None


__all__ = [
    "RedisCache",
    "close_redis_cache",
    "get_redis_cache",
    "initialize_redis_cache",
]
