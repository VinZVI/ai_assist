"""
@file: log_lexicon/ai_providers.py
@description: Лог-сообщения для AI провайдеров
@created: 2025-10-03
"""

# Лог-сообщения для AI провайдеров
AI_PROVIDER_INITIALIZED = "🔧 Провайдер {provider} инициализирован"
AI_PROVIDER_CLIENT_CREATED = "🔗 HTTP клиент для {provider} создан"
AI_PROVIDER_CONFIG_CHECK = "🔍 Проверка конфигурации {provider} провайдера"
AI_PROVIDER_CONFIG_VALID = "✅ Конфигурация {provider} провайдера валидна"
AI_PROVIDER_CONFIG_INVALID = "❌ Конфигурация {provider} провайдера невалидна: {error}"
AI_PROVIDER_REQUEST_SENT = "🚀 Отправка запроса к {provider} API (попытка {attempt})"
AI_PROVIDER_RESPONSE_RECEIVED = "✅ Ответ от {provider} API получен за {duration:.2f}с"
AI_PROVIDER_ERROR_OCCURRED = "❌ Ошибка провайдера {provider}: {error}"
AI_PROVIDER_FALLBACK_TRIGGERED = (
    "🔄 Переключение на резервный провайдер из-за ошибки {provider}"
)
AI_PROVIDER_RETRY_DELAY = "⏳ Ожидание {delay}с перед повторной попыткой к {provider}"
AI_PROVIDER_CACHE_HIT = "🎯 Найден кешированный ответ для {provider}"
AI_PROVIDER_CACHE_MISS = "🔍 Кешированный ответ не найден для {provider}"
AI_PROVIDER_CACHE_STORED = "💾 Ответ сохранен в кеш для {provider}"
AI_PROVIDER_HEALTH_CHECK_START = "🏥 Начало проверки состояния {provider}"
AI_PROVIDER_HEALTH_CHECK_OK = "✅ Провайдер {provider} доступен"
AI_PROVIDER_HEALTH_CHECK_FAIL = "❌ Провайдер {provider} недоступен: {error}"
