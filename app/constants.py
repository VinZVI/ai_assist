"""
@file: constants.py
@description: Константы и сообщения об ошибках для всего приложения (УСТАРЕЛ - ИСПОЛЬЗУЙТЕ МОДУЛЬНЫЕ ФАЙЛЫ)
@created: 2025-09-27
"""

# ПРЕДУПРЕЖДЕНИЕ: Этот файл устарел!
# Используйте модульные файлы констант из app/constants/:
# - app/constants/config.py для конфигурации
# - app/constants/errors.py для ошибок
# и т.д.

import warnings

warnings.warn(
    "app/constants.py устарел. Используйте модульные файлы из app/constants/.",
    DeprecationWarning,
    stacklevel=2,
)


# Сообщения об ошибках для конфигурации
class ConfigErrorMessages:
    """Сообщения об ошибках конфигурации."""

    # Telegram
    INVALID_BOT_TOKEN_FORMAT = "BOT_TOKEN must be set to a valid Telegram bot token"
    INVALID_BOT_TOKEN_STRUCTURE = "BOT_TOKEN must be in format 'number:hash'"

    # DeepSeek
    INVALID_DEEPSEEK_API_KEY = "DEEPSEEK_API_KEY must be set to a valid API key"
    INVALID_DEEPSEEK_TEMPERATURE = "DEEPSEEK_TEMPERATURE must be between 0.0 and 2.0"
    INVALID_DEEPSEEK_MAX_TOKENS = "DEEPSEEK_MAX_TOKENS must be between 1 and 4000"

    # OpenRouter
    INVALID_OPENROUTER_API_KEY = "OPENROUTER_API_KEY cannot be empty"
    INVALID_OPENROUTER_TEMPERATURE = (
        "OPENROUTER_TEMPERATURE must be between 0.0 and 2.0"
    )
    INVALID_OPENROUTER_MAX_TOKENS = "OPENROUTER_MAX_TOKENS must be between 1 and 8000"

    # User Limits
    INVALID_FREE_MESSAGES_LIMIT = "FREE_MESSAGES_LIMIT must be positive"
    INVALID_PREMIUM_PRICE = "PREMIUM_PRICE must be positive"
    INVALID_FREE_MESSAGES_LIMIT_NON_NEGATIVE = (
        "FREE_MESSAGES_LIMIT must be non-negative"
    )

    # Admin
    INVALID_ADMIN_USER_ID = "ADMIN_USER_ID must be positive"
    INVALID_ADMIN_USER_ID_POSITIVE = "ADMIN_USER_ID must be a positive integer"

    # Payment
    INVALID_PAYMENT_PROVIDER = (
        "PAYMENT_PROVIDER must be one of: ['telegram_stars', 'yookassa']"
    )

    # Cache
    INVALID_CACHE_TTL = "CACHE_TTL must be positive"

    # Rate Limit
    INVALID_RATE_LIMIT_VALUE = "Rate limit values must be positive"

    # Logging
    INVALID_LOG_LEVEL = (
        "LOG_LEVEL must be one of: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']"
    )

    # Security
    INVALID_SECRET_KEY = "SECRET_KEY must be set to a secure random string"
    SECRET_KEY_TOO_SHORT = "SECRET_KEY must be at least 32 characters long"

    # AI Provider
    INVALID_AI_PROVIDER = "Provider must be one of: ['deepseek', 'openrouter']"
    INVALID_AI_PROVIDER_RETRIES_FORMAT = (
        "AI_MAX_RETRIES_PER_PROVIDER must be between {min_retries} and {max_retries}"
    )


# Магические значения для конфигурации
class ConfigMagicValues:
    """Магические значения, используемые в конфигурации."""

    # DeepSeek
    DEEPSEEK_DEFAULT_TEMPERATURE = 0.7
    DEEPSEEK_DEFAULT_MAX_TOKENS = 1000
    DEEPSEEK_DEFAULT_TIMEOUT = 30
    DEEPSEEK_MIN_TEMPERATURE = 0.0
    DEEPSEEK_MAX_TEMPERATURE = 2.0
    DEEPSEEK_MIN_MAX_TOKENS = 1
    DEEPSEEK_MAX_MAX_TOKENS_DEEPSEEK = 4000

    # Database
    DATABASE_DEFAULT_POOL_SIZE = 10
    DATABASE_DEFAULT_TIMEOUT = 30
    DATABASE_DEFAULT_PORT = 5432

    # OpenRouter
    OPENROUTER_DEFAULT_TIMEOUT = 30
    OPENROUTER_DEFAULT_MAX_TOKENS = 1000
    OPENROUTER_DEFAULT_TEMPERATURE = 0.7
    OPENROUTER_MIN_TEMPERATURE = 0.0
    OPENROUTER_MAX_TEMPERATURE = 2.0
    OPENROUTER_MIN_MAX_TOKENS = 1
    DEEPSEEK_MAX_MAX_TOKENS_OPENROUTER = 8000

    # User Limits
    DEFAULT_FREE_MESSAGES_LIMIT = 10
    DEFAULT_PREMIUM_PRICE = 99
    DEFAULT_PREMIUM_DURATION_DAYS = 30
    DEFAULT_ADMIN_USER_ID = 123456789

    # Cache
    DEFAULT_CACHE_TTL = 3600

    # Rate Limit
    DEFAULT_RATE_LIMIT_PER_MINUTE = 60
    DEFAULT_RATE_LIMIT_BLOCK_TIME = 300

    # Security
    MIN_SECRET_KEY_LENGTH = 32

    # AI Provider
    AI_PROVIDER_MAX_RETRIES = 3
    AI_PROVIDER_TIMEOUT = 30

    # Validation
    AI_PROVIDER_MAX_RETRIES_MIN = 1
    AI_PROVIDER_MAX_RETRIES_MAX = 10
