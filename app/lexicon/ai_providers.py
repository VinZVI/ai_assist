"""
@file: lexicon/ai_providers.py
@description: Лексикон для AI провайдеров
@created: 2025-10-03
"""

# Общие сообщения для AI провайдеров
AI_PROVIDER_INITIALIZING = "🔧 Инициализация {provider} провайдера..."
AI_PROVIDER_HTTP_CLIENT_CREATED = "🔗 HTTP клиент для {provider} API создан"
AI_PROVIDER_CONFIGURED = "✅ {provider} провайдер настроен"
AI_PROVIDER_NOT_CONFIGURED = "⚠️ {provider} провайдер не настроен"
AI_PROVIDER_AVAILABLE = "✅ {provider} API доступен"
AI_PROVIDER_UNAVAILABLE = "❌ {provider} API недоступен: {error}"
AI_PROVIDER_RESPONSE = (
    "🤖 {provider} ответ: {chars} символов, {tokens} токенов, {duration}s"
)
AI_PROVIDER_REQUEST_ERROR = "❌ Ошибка запроса к {provider}: {error}"
AI_PROVIDER_TIMEOUT = "⏰ Таймаут запроса к {provider} ({timeout}s)"
AI_PROVIDER_RATE_LIMIT = "🚦 Превышен лимит запросов к {provider}, ожидание {delay}s"
AI_PROVIDER_INVALID_RESPONSE = "⚠️ Невалидный ответ от {provider}: {error}"

# Сообщения для DeepSeek провайдера
DEEPSEEK_PROVIDER_NAME = "DeepSeek"
DEEPSEEK_INVALID_API_KEY = "Неверный API ключ DeepSeek"
DEEPSEEK_QUOTA_EXCEEDED = "Недостаточно средств на счете DeepSeek API. Пополните баланс в личном кабинете DeepSeek."
DEEPSEEK_RATE_LIMIT = "Превышен лимит запросов к DeepSeek API"
DEEPSEEK_CONNECTION_ERROR = "Не удалось подключиться к DeepSeek API"
DEEPSEEK_TIMEOUT_ERROR = "Timeout при обращении к DeepSeek API"
DEEPSEEK_SERVER_ERROR = "Ошибка сервера DeepSeek: {status_code}"
DEEPSEEK_UNEXPECTED_STATUS = (
    "Неожиданный статус ответа DeepSeek: {status_code}. {error_text}"
)
DEEPSEEK_RETRYING = "🔄 Ошибка сервера DeepSeek {status_code}. Повтор через {delay}с..."

# Сообщения для OpenRouter провайдера
OPENROUTER_PROVIDER_NAME = "OpenRouter"
OPENROUTER_INVALID_API_KEY = "Неверный API ключ OpenRouter"
OPENROUTER_QUOTA_EXCEEDED = "Недостаточно средств на счете OpenRouter API. Пополните баланс в личном кабинете OpenRouter."
OPENROUTER_RATE_LIMIT = "Превышен лимит запросов к OpenRouter API"
OPENROUTER_CONNECTION_ERROR = "Не удалось подключиться к OpenRouter API"
OPENROUTER_TIMEOUT_ERROR = "Timeout при обращении к OpenRouter API"
OPENROUTER_SERVER_ERROR = "Ошибка сервера OpenRouter: {status_code}"
OPENROUTER_UNEXPECTED_STATUS = (
    "Неожиданный статус ответа OpenRouter: {status_code}. {error_text}"
)
OPENROUTER_RETRYING = (
    "🔄 Ошибка сервера OpenRouter {status_code}. Повтор через {delay}с..."
)

# Сообщения для AI менеджера
AI_MANAGER_INITIALIZING = "🔧 Инициализация AI провайдеров..."
AI_MANAGER_DEEPSEEK_INITIALIZED = "✅ DeepSeek провайдер инициализирован"
AI_MANAGER_OPENROUTER_INITIALIZED = "✅ OpenRouter провайдер инициализирован"
AI_MANAGER_ACTIVE_PROVIDERS = "🎯 Активные провайдеры: {providers}"
AI_MANAGER_INITIALIZED = "🤖 AI менеджер инициализирован"
AI_MANAGER_PROVIDER_ATTEMPT = "🎯 Попытка {attempt}: использование {provider}"
AI_MANAGER_REQUEST = "🚀 Запрос к {provider}..."
AI_MANAGER_RESPONSE_RECEIVED = "✅ Успешный ответ от {provider} API за {duration}s"
AI_MANAGER_ERROR = "❌ Ошибка при запросе к {provider}: {error}"
AI_MANAGER_FALLBACK = "🔄 Использование резервного провайдера {fallback_provider}"
AI_MANAGER_ALL_PROVIDERS_FAILED = "💥 Все провайдеры недоступны"
AI_MANAGER_HEALTH_CHECK = "🏥 Проверка состояния провайдеров..."
AI_MANAGER_HEALTH_CHECK_RESULT = "📊 Результаты проверки: {results}"
AI_MANAGER_CACHE_CLEARED = "🧹 Кеш AI менеджера очищен"
AI_MANAGER_SHUTTING_DOWN = "🛑 Завершение работы AI менеджера..."
AI_MANAGER_SHUTDOWN_COMPLETED = "✅ AI менеджер завершил работу"
AI_MANAGER_SHUTDOWN_ERROR = "❌ Ошибка при завершении работы AI менеджера: {error}"
