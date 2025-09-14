"""
@file: config.py
@description: Конфигурация приложения с валидацией через Pydantic
@dependencies: pydantic, python-dotenv
@created: 2025-09-07
"""

from pathlib import Path

from loguru import logger
from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    """Конфигурация базы данных."""

    # Полный URL или отдельные параметры
    database_url: str | None = Field(default=None, env="DATABASE_URL")
    database_host: str = Field(default="localhost", env="DATABASE_HOST")
    database_port: int = Field(default=5432, env="DATABASE_PORT")
    database_name: str = Field(default="ai_assist", env="DATABASE_NAME")
    database_user: str = Field(default="postgres", env="DATABASE_USER")
    database_password: str = Field(default="password", env="DATABASE_PASSWORD")

    # Настройки пула соединений
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    database_timeout: int = Field(default=30, env="DATABASE_TIMEOUT")

    model_config = {"extra": "ignore", "env_file": ".env"}

    @field_validator("database_url", mode="before")
    @classmethod
    def build_database_url(cls, v: str | None, info: ValidationInfo) -> str:
        """Построение URL БД из отдельных параметров если не задан полный URL."""
        if v is not None:
            return v

        # Получаем значения из info.data если они доступны
        values = info.data if hasattr(info, "data") else {}
        user = values.get("database_user", "postgres")
        password = values.get("database_password", "password")
        host = values.get("database_host", "localhost")
        port = values.get("database_port", 5432)
        database = values.get("database_name", "ai_assist")

        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"


class TelegramConfig(BaseSettings):
    """Конфигурация Telegram бота."""

    bot_token: str = Field(env="BOT_TOKEN")
    webhook_url: str | None = Field(default=None, env="WEBHOOK_URL")
    webhook_secret: str | None = Field(default=None, env="WEBHOOK_SECRET")
    use_polling: bool = Field(default=True, env="USE_POLLING")

    model_config = {"extra": "ignore", "env_file": ".env"}

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
            raise ValueError("BOT_TOKEN must be set to a valid Telegram bot token")

        # Базовая проверка формата токена (number:hash)
        if ":" not in v:
            raise ValueError("BOT_TOKEN must be in format 'number:hash'")

        return v


class DeepSeekConfig(BaseSettings):
    """Конфигурация DeepSeek API."""

    deepseek_api_key: str = Field(env="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", env="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field(default="deepseek-chat", env="DEEPSEEK_MODEL")
    deepseek_max_tokens: int = Field(default=1000, env="DEEPSEEK_MAX_TOKENS")
    deepseek_temperature: float = Field(default=0.7, env="DEEPSEEK_TEMPERATURE")
    deepseek_timeout: int = Field(default=30, env="DEEPSEEK_TIMEOUT")

    model_config = {"extra": "ignore", "env_file": ".env"}

    @field_validator("deepseek_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Валидация API ключа DeepSeek."""
        if not v or v == "your_deepseek_api_key_here":
            raise ValueError("DEEPSEEK_API_KEY must be set to a valid API key")
        return v

    @field_validator("deepseek_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Валидация температуры генерации."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("DEEPSEEK_TEMPERATURE must be between 0.0 and 2.0")
        return v

    @field_validator("deepseek_max_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        """Валидация максимального количества токенов."""
        if v <= 0 or v > 4000:
            raise ValueError("DEEPSEEK_MAX_TOKENS must be between 1 and 4000")
        return v


class UserLimitsConfig(BaseSettings):
    """Конфигурация лимитов пользователей."""

    free_messages_limit: int = Field(default=10, env="FREE_MESSAGES_LIMIT")
    premium_price: int = Field(default=99, env="PREMIUM_PRICE")
    premium_duration_days: int = Field(default=30, env="PREMIUM_DURATION_DAYS")

    model_config = {"extra": "ignore", "env_file": ".env"}

    @field_validator("free_messages_limit")
    @classmethod
    def validate_free_limit(cls, v: int) -> int:
        """Валидация лимита бесплатных сообщений."""
        if v < 0:
            raise ValueError("FREE_MESSAGES_LIMIT must be non-negative")
        return v

    @field_validator("premium_price")
    @classmethod
    def validate_premium_price(cls, v: int) -> int:
        """Валидация цены премиум доступа."""
        if v <= 0:
            raise ValueError("PREMIUM_PRICE must be positive")
        return v


class AdminConfig(BaseSettings):
    """Конфигурация администраторов."""

    admin_user_id: int = Field(env="ADMIN_USER_ID")
    admin_user_ids: str | None = Field(default=None, env="ADMIN_USER_IDS")

    model_config = {"extra": "ignore", "env_file": ".env"}

    @field_validator("admin_user_id")
    @classmethod
    def validate_admin_id(cls, v: int) -> int:
        """Валидация ID администратора."""
        if v <= 0:
            raise ValueError("ADMIN_USER_ID must be a positive integer")
        return v

    def get_admin_ids(self) -> list[int]:
        """Получение списка всех ID администраторов."""
        admin_ids = [self.admin_user_id]

        if self.admin_user_ids:
            try:
                additional_ids = [
                    int(uid.strip())
                    for uid in self.admin_user_ids.split(",")
                    if uid.strip()
                ]
                admin_ids.extend(additional_ids)
            except ValueError:
                # Логируем ошибку, но не падаем
                pass

        return list(set(admin_ids))  # Убираем дубликаты


class PaymentConfig(BaseSettings):
    """Конфигурация платежей."""

    payment_provider: str = Field(default="telegram_stars", env="PAYMENT_PROVIDER")
    payment_provider_token: str | None = Field(default=None, env="PAYMENT_PROVIDER_TOKEN")

    model_config = {"extra": "ignore", "env_file": ".env"}

    @field_validator("payment_provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Валидация провайдера платежей."""
        allowed_providers = ["telegram_stars", "yookassa"]
        if v not in allowed_providers:
            raise ValueError(f"PAYMENT_PROVIDER must be one of: {allowed_providers}")
        return v


class RedisConfig(BaseSettings):
    """Конфигурация Redis (опционально)."""

    redis_url: str | None = Field(default=None, env="REDIS_URL")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")

    model_config = {"extra": "ignore", "env_file": ".env"}

    @field_validator("cache_ttl")
    @classmethod
    def validate_ttl(cls, v: int) -> int:
        """Валидация времени жизни кеша."""
        if v <= 0:
            raise ValueError("CACHE_TTL must be positive")
        return v


class MonitoringConfig(BaseSettings):
    """Конфигурация мониторинга."""

    enable_request_logging: bool = Field(default=False, env="ENABLE_REQUEST_LOGGING")
    enable_metrics: bool = Field(default=False, env="ENABLE_METRICS")
    sentry_dsn: str | None = Field(default=None, env="SENTRY_DSN")

    model_config = {"extra": "ignore", "env_file": ".env"}


class RateLimitConfig(BaseSettings):
    """Конфигурация ограничения скорости запросов."""

    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_block_time: int = Field(default=300, env="RATE_LIMIT_BLOCK_TIME")

    model_config = {"extra": "ignore", "env_file": ".env"}

    @field_validator("rate_limit_per_minute", "rate_limit_block_time")
    @classmethod
    def validate_positive(cls, v: int) -> int:
        """Валидация положительных значений."""
        if v <= 0:
            raise ValueError("Rate limit values must be positive")
        return v


class AppConfig(BaseSettings):
    """Главная конфигурация приложения."""

    # Основные настройки
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    secret_key: str = Field(env="SECRET_KEY")
    timezone: str = Field(default="Europe/Moscow", env="TIMEZONE")
    auto_reload: bool = Field(default=True, env="AUTO_RELOAD")
    show_debug_info: bool = Field(default=False, env="SHOW_DEBUG_INFO")

    # Вложенные конфигурации (создаются лениво)
    database: DatabaseConfig | None = None
    telegram: TelegramConfig | None = None
    deepseek: DeepSeekConfig | None = None
    user_limits: UserLimitsConfig | None = None
    admin: AdminConfig | None = None
    payment: PaymentConfig | None = None
    redis: RedisConfig | None = None
    monitoring: MonitoringConfig | None = None
    rate_limit: RateLimitConfig | None = None

    def __init__(self, **data):
        super().__init__(**data)
        # Создаем экземпляры вложенных конфигураций
        self.database = DatabaseConfig()
        self.telegram = TelegramConfig()
        self.deepseek = DeepSeekConfig()
        self.user_limits = UserLimitsConfig()
        self.admin = AdminConfig()
        self.payment = PaymentConfig()
        self.redis = RedisConfig()
        self.monitoring = MonitoringConfig()
        self.rate_limit = RateLimitConfig()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Валидация уровня логирования."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {allowed_levels}")
        return v_upper

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Валидация секретного ключа."""
        if not v or v == "your_secret_key_here":
            raise ValueError("SECRET_KEY must be set to a secure random string")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # Игнорируем дополнительные поля из .env
    }



# Глобальный экземпляр конфигурации (создается лениво)
_config_instance: AppConfig | None = None

def get_config() -> AppConfig:
    """Получение экземпляра конфигурации приложения."""
    global _config_instance

    if _config_instance is None:
        # Загружаем .env файл если он существует
        env_file = Path(".env")
        if env_file.exists():
            _config_instance = AppConfig(_env_file=str(env_file))
        else:
            _config_instance = AppConfig()

        logger.info("✅ Конфигурация приложения загружена успешно")

    return _config_instance


# Экспорт для удобного использования
__all__ = [
    "AdminConfig",
    "AppConfig",
    "DatabaseConfig",
    "DeepSeekConfig",
    "MonitoringConfig",
    "PaymentConfig",
    "RateLimitConfig",
    "RedisConfig",
    "TelegramConfig",
    "UserLimitsConfig",
    "get_config",
]
