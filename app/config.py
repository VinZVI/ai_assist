"""
@file: config.py
@description: Конфигурация приложения с валидацией через Pydantic
@dependencies: pydantic, python-dotenv
@created: 2025-09-07
"""

from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from app.constants.config import ConfigErrorMessages, ConfigMagicValues
from app.lexicon.gettext import get_log_text


class DatabaseConfig(BaseSettings):
    """Конфигурация базы данных."""

    # Отдельные параметры (обязательные)
    database_host: str = Field(default="localhost", validation_alias="DATABASE_HOST")
    database_port: int = Field(default=5432, validation_alias="DATABASE_PORT")
    database_name: str = Field(default="ai_assist", validation_alias="DATABASE_NAME")
    database_user: str = Field(default="postgres", validation_alias="DATABASE_USER")
    database_password: str = Field(
        default="password", validation_alias="DATABASE_PASSWORD"
    )

    # Настройки пула соединений
    database_pool_size: int = Field(
        default=20, validation_alias="DATABASE_POOL_SIZE"
    )  # Увеличиваем с 10 до 20
    database_timeout: int = Field(default=30, validation_alias="DATABASE_TIMEOUT")

    model_config = {"extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def database_url(self) -> str:
        """Построение URL БД из отдельных параметров."""
        return f"postgresql+asyncpg://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"


class TelegramConfig(BaseSettings):
    """Конфигурация Telegram бота."""

    bot_token: str = Field(
        default="your_telegram_bot_token_here", validation_alias="BOT_TOKEN"
    )
    webhook_url: str | None = Field(default=None, validation_alias="WEBHOOK_URL")
    webhook_secret: str | None = Field(default=None, validation_alias="WEBHOOK_SECRET")
    use_polling: bool = Field(default=True, validation_alias="USE_POLLING")

    model_config = {"extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}

    @field_validator("webhook_url", mode="before")
    @classmethod
    def validate_webhook_url(cls, v: str | None) -> str | None:
        """Валидация webhook URL, поддерживающая пустые значения."""
        if v == "" or v is None:
            return None
        return v

    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """Валидация формата токена бота."""
        if not v or v == "your_telegram_bot_token_here":
            raise ValueError(ConfigErrorMessages.INVALID_BOT_TOKEN_FORMAT)

        # Базовая проверка формата токена (number:hash)
        if ":" not in v:
            raise ValueError(ConfigErrorMessages.INVALID_BOT_TOKEN_STRUCTURE)

        return v


class OpenRouterConfig(BaseSettings):
    """Конфигурация OpenRouter API."""

    openrouter_api_key: str = Field(
        default="your_openrouter_api_key_here", validation_alias="OPENROUTER_API_KEY"
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", validation_alias="OPENROUTER_BASE_URL"
    )
    openrouter_models: list[str] = Field(
        default=["openrouter/default-model"], validation_alias="OPENROUTER_MODEL"
    )
    openrouter_max_tokens: int = Field(
        default=1000, validation_alias="OPENROUTER_MAX_TOKENS"
    )
    openrouter_temperature: float = Field(
        default=0.7, validation_alias="OPENROUTER_TEMPERATURE"
    )
    openrouter_timeout: int = Field(default=30, validation_alias="OPENROUTER_TIMEOUT")
    openrouter_site_url: str = Field(
        default="https://ai-assist.example.com", validation_alias="OPENROUTER_SITE_URL"
    )
    openrouter_app_name: str = Field(
        default="AI-Assistant", validation_alias="OPENROUTER_APP_NAME"
    )

    model_config = {"extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}

    @field_validator("openrouter_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Валидация API ключа OpenRouter."""
        # Пока просто проверяем, что ключ не пустой
        if not v:
            raise ValueError(ConfigErrorMessages.INVALID_OPENROUTER_API_KEY)
        return v

    @field_validator("openrouter_models", mode="before")
    @classmethod
    def validate_models(cls, v: str | list[str]) -> list[str]:
        """Валидация списка моделей OpenRouter."""
        if isinstance(v, str):
            # Try to parse as JSON array
            import json

            try:
                parsed = json.loads(
                    v.replace("'", '"')
                )  # Replace single quotes with double
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                # If JSON parsing fails, treat as single model
                return [v.strip().strip('"')]
        elif isinstance(v, list):
            return v
        return ["openrouter/default-model"]

    def is_configured(self) -> bool:
        """Проверка, настроен ли OpenRouter."""
        return self.openrouter_api_key != "your_openrouter_api_key_here"

    @field_validator("openrouter_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Валидация температуры генерации."""
        min_temp = ConfigMagicValues.OPENROUTER_MIN_TEMPERATURE
        max_temp = ConfigMagicValues.OPENROUTER_MAX_TEMPERATURE
        if not min_temp <= v <= max_temp:
            raise ValueError(ConfigErrorMessages.INVALID_OPENROUTER_TEMPERATURE)
        return v

    @field_validator("openrouter_max_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        """Валидация максимального количества токенов."""
        min_tokens = ConfigMagicValues.OPENROUTER_MIN_MAX_TOKENS
        max_tokens = ConfigMagicValues.OPENROUTER_MAX_MAX_TOKENS
        if v < min_tokens or v > max_tokens:  # OpenRouter поддерживает больше токенов
            raise ValueError(ConfigErrorMessages.INVALID_OPENROUTER_MAX_TOKENS)
        return v


class AIProviderConfig(BaseSettings):
    """Конфигурация провайдеров AI."""

    primary_provider: str = Field(
        default="openrouter", validation_alias="AI_PRIMARY_PROVIDER"
    )
    enable_fallback: bool = Field(default=True, validation_alias="AI_ENABLE_FALLBACK")

    model_config = {"extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}


class UserLimitsConfig(BaseSettings):
    """Конфигурация лимитов пользователей."""

    free_messages_limit: int = Field(default=5, validation_alias="FREE_MESSAGES_LIMIT")
    premium_duration_days: int = Field(
        default=30, validation_alias="PREMIUM_DURATION_DAYS"
    )
    premium_price: int = Field(default=100, validation_alias="PREMIUM_PRICE")
    premium_message_limit: int = Field(
        default=100, validation_alias="PREMIUM_MESSAGE_LIMIT"
    )

    # New configuration parameters for anti-spam and rate limiting
    spam_actions_per_minute: int = Field(
        default=20, validation_alias="SPAM_ACTIONS_PER_MINUTE"
    )
    spam_restriction_duration: int = Field(
        default=10, validation_alias="SPAM_RESTRICTION_DURATION"
    )
    daily_message_limit: int = Field(default=20, validation_alias="DAILY_MESSAGE_LIMIT")

    model_config = {"extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}


class PaymentConfig(BaseSettings):
    """Конфигурация платежей."""

    enabled: bool = Field(default=True, validation_alias="PAYMENT_ENABLED")
    provider: str = Field(default="telegram_stars", validation_alias="PAYMENT_PROVIDER")
    test_mode: bool = Field(default=False, validation_alias="PAYMENT_TEST_MODE")

    model_config = {"extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}


class MonitoringConfig(BaseSettings):
    """Конфигурация мониторинга."""

    health_check_inactivity_hours: int = Field(
        default=6, validation_alias="HEALTH_CHECK_INACTIVITY_HOURS"
    )
    health_check_interval: int = Field(
        default=60, validation_alias="HEALTH_CHECK_INTERVAL"
    )

    model_config = {"extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}


class CacheConfig(BaseSettings):
    """Конфигурация кэширования."""

    ttl: int = Field(default=3600, validation_alias="CACHE_TTL")
    redis_host: str = Field(default="localhost", validation_alias="REDIS_HOST")
    redis_port: int = Field(default=6379, validation_alias="REDIS_PORT")
    redis_username: str | None = Field(default=None, validation_alias="REDIS_USERNAME")
    redis_password: str | None = Field(default=None, validation_alias="REDIS_PASSWORD")

    model_config = {"extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def redis_url(self) -> str:
        """Построение URL Redis из отдельных параметров."""
        if self.redis_username and self.redis_password:
            return f"redis://{self.redis_username}:{self.redis_password}@{self.redis_host}:{self.redis_port}"
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}"
        return f"redis://{self.redis_host}:{self.redis_port}"


class ConversationConfig(BaseSettings):
    """Конфигурация диалогов."""

    enable_saving: bool = Field(
        default=False, validation_alias="CONVERSATION_ENABLE_SAVING"
    )

    model_config = {"extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}


class AdminConfig(BaseSettings):
    """Конфигурация администраторов."""

    admin_user_id: int = Field(default=123456789, validation_alias="ADMIN_USER_ID")
    admin_user_ids: str = Field(default="", validation_alias="ADMIN_USER_IDS")

    model_config = {"extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}

    @field_validator("admin_user_id")
    @classmethod
    def validate_admin_user_id(cls, v: int) -> int:
        """Валидация ID администратора."""
        if v <= 0:
            raise ValueError(ConfigErrorMessages.INVALID_ADMIN_USER_ID_POSITIVE)
        return v

    def get_admin_ids(self) -> list[int]:
        """Получение списка ID администраторов."""
        admin_ids = [self.admin_user_id]

        if self.admin_user_ids:
            # Разбиваем строку по запятым и конвертируем в int
            additional_ids = [
                int(user_id.strip())
                for user_id in self.admin_user_ids.split(",")
                if user_id.strip().isdigit()
            ]
            admin_ids.extend(additional_ids)

        # Удаляем дубликаты и возвращаем список
        return list(set(admin_ids))


class AppConfig(BaseSettings):
    """Основная конфигурация приложения."""

    # Компоненты конфигурации
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    openrouter: OpenRouterConfig = Field(default_factory=OpenRouterConfig)
    ai_provider: AIProviderConfig = Field(default_factory=AIProviderConfig)
    user_limits: UserLimitsConfig = Field(default_factory=UserLimitsConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    conversation: ConversationConfig = Field(default_factory=ConversationConfig)
    admin: AdminConfig = Field(default_factory=AdminConfig)
    payment: PaymentConfig = Field(default_factory=PaymentConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    # Дополнительные настройки
    debug: bool = Field(default=False, validation_alias="DEBUG")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    model_config = {"extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}

    def __init__(self, **data: Any) -> None:
        """Инициализация конфигурации с логированием."""
        super().__init__(**data)
        logger.info(get_log_text("config.config_loaded_success"))


class ConfigManager:
    """Менеджер конфигурации приложения с паттерном Singleton."""

    _instance: "ConfigManager | None" = None
    _config: AppConfig | None = None

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_config(self) -> AppConfig:
        """Получение экземпляра конфигурации приложения."""
        if self._config is None:
            self._config = AppConfig()
        return self._config

    def reset_config(self) -> None:
        """Сброс экземпляра конфигурации (для тестирования)."""
        self._config = None


# Глобальный экземпляр менеджера конфигурации
_config_manager = ConfigManager()


def get_config() -> AppConfig:
    """
    Получение глобальной конфигурации приложения (Singleton).

    Returns:
        AppConfig: Объект конфигурации приложения
    """
    return _config_manager.get_config()


__all__ = [
    "AIProviderConfig",
    "AdminConfig",
    "AppConfig",
    "CacheConfig",
    "ConfigManager",
    "DatabaseConfig",
    "OpenRouterConfig",
    "TelegramConfig",
    "UserLimitsConfig",
    "_config_manager",
    "get_config",
]
