"""
@file: lexicon/utils.py
@description: Лексикон для утилит
@created: 2025-10-03
"""

# Сообщения для системы логирования
LOGGING_SYSTEM_INITIALIZED = "🚀 Система логирования инициализирована"
LOGGING_LEVEL_SET = "📊 Уровень логирования: {level}"
LOGGING_JSON_ENABLED = "📁 JSON формат: включен"
LOGGING_JSON_DISABLED = "📁 JSON формат: отключен"
LOGGING_CONSOLE_ENABLED = "📋 Консольный вывод: включен"
LOGGING_CONSOLE_DISABLED = "📋 Консольный вывод: отключен"
LOGGING_REQUEST_ENABLED = "🌐 Логирование запросов: включено"
LOGGING_REQUEST_DISABLED = "🌐 Логирование запросов: отключено"

# Сообщения для валидаторов
VALIDATOR_INVALID_BOT_TOKEN = "BOT_TOKEN must be set to a valid Telegram bot token"
VALIDATOR_INVALID_BOT_TOKEN_FORMAT = "BOT_TOKEN must be in format 'number:hash'"
VALIDATOR_INVALID_DEEPSEEK_API_KEY = "DEEPSEEK_API_KEY must be set to a valid API key"
VALIDATOR_INVALID_DEEPSEEK_TEMPERATURE = (
    "DEEPSEEK_TEMPERATURE must be between 0.0 and 2.0"
)
VALIDATOR_INVALID_DEEPSEEK_MAX_TOKENS = "DEEPSEEK_MAX_TOKENS must be between 1 and 4000"
VALIDATOR_INVALID_OPENROUTER_API_KEY = "OPENROUTER_API_KEY cannot be empty"
VALIDATOR_INVALID_OPENROUTER_TEMPERATURE = (
    "OPENROUTER_TEMPERATURE must be between 0.0 and 2.0"
)
VALIDATOR_INVALID_OPENROUTER_MAX_TOKENS = (
    "OPENROUTER_MAX_TOKENS must be between 1 and 8000"
)
