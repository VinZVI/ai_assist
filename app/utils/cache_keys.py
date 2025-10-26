import hashlib
import json
from typing import Any

from loguru import logger


class CacheKeyManager:
    """Централизованное управление ключами кэша."""

    # Префиксы для разных типов данных
    PREFIXES = {
        "user": "user",
        "conversation_context": "conv_ctx",
        "conversation_backup": "conv_backup",
        "user_stats": "user_stats",
        "system_stats": "sys_stats",
        "rate_limit": "rate_limit",
        "anti_spam": "anti_spam",
    }

    VERSION = "v1"  # Версия схемы ключей для миграций

    @classmethod
    def user_key(cls, telegram_id: int) -> str:
        """Ключ для пользователя."""
        return f"{cls.PREFIXES['user']}:{cls.VERSION}:{telegram_id}"

    @classmethod
    def conversation_context_key(
        cls, user_id: int, limit: int = 6, max_age_hours: int = 12
    ) -> str:
        """Ключ для контекста диалога."""
        return f"{cls.PREFIXES['conversation_context']}:{cls.VERSION}:{user_id}:{limit}:{max_age_hours}"

    @classmethod
    def conversation_backup_key(cls, user_id: int) -> str:
        """Ключ для бэкапа диалога."""
        return f"{cls.PREFIXES['conversation_backup']}:{cls.VERSION}:{user_id}"

    @classmethod
    def user_stats_key(cls, date_str: str | None = None) -> str:
        """Ключ для статистики пользователей."""
        date_part = date_str or "current"
        return f"{cls.PREFIXES['user_stats']}:{cls.VERSION}:{date_part}"

    @classmethod
    def rate_limit_key(cls, user_id: int, window_type: str = "minute") -> str:
        """Ключ для rate limiting."""
        return f"{cls.PREFIXES['rate_limit']}:{cls.VERSION}:{user_id}:{window_type}"

    @classmethod
    def anti_spam_key(cls, user_id: int) -> str:
        """Ключ для anti-spam."""
        return f"{cls.PREFIXES['anti_spam']}:{cls.VERSION}:{user_id}"

    @classmethod
    def generate_hash_key(cls, prefix: str, data: dict[str, Any]) -> str:
        """Генерация ключа на основе хеша данных."""
        # Сортируем ключи для консистентности
        sorted_data = json.dumps(data, sort_keys=True, ensure_ascii=False)
        hash_value = hashlib.md5(sorted_data.encode()).hexdigest()[:16]
        return f"{prefix}:{cls.VERSION}:hash:{hash_value}"

    @classmethod
    def parse_key(cls, key: str) -> dict[str, Any]:
        """Разбор ключа кэша."""
        try:
            parts = key.split(":")
            if len(parts) < 3:
                return {"valid": False, "error": "Invalid key format"}

            return {
                "valid": True,
                "prefix": parts[0],
                "version": parts[1],
                "components": parts[2:],
                "full_key": key,
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    @classmethod
    def get_migration_pattern(cls, old_version: str, prefix: str) -> str:
        """Паттерн для поиска ключей старой версии при миграции."""
        return f"{prefix}:{old_version}:*"
