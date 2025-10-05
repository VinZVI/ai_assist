"""
@file: constants/errors.py
@description: Константы и сообщения об ошибках для всего приложения
@created: 2025-10-03
"""

# Общие сообщения об ошибках
GENERAL_ERROR = "❌ Произошла ошибка. Попробуйте повторить запрос позже."
UNEXPECTED_ERROR = "💥 Неожиданная ошибка: {error}"

# Сообщения об ошибках для базы данных
DB_CONNECTION_ERROR = "❌ Ошибка подключения к базе данных: {error}"
DB_INTEGRITY_ERROR = "❌ Ошибка целостности при работе с базой данных: {error}"
DB_SQLALCHEMY_ERROR = "❌ Ошибка SQLAlchemy: {error}"

# Сообщения об ошибках для AI провайдеров
AI_PROVIDER_ERROR = "❌ Ошибка AI провайдера {provider}: {error}"
AI_QUOTA_ERROR = "Недостаточно средств на счете {provider} API. Пополните баланс в личном кабинете {provider}."
AI_AUTH_ERROR = "Неверный API ключ {provider}"
AI_RATE_LIMIT_ERROR = "Превышен лимит запросов к {provider} API"
AI_CONNECTION_ERROR = "Не удалось подключиться к {provider} API"
AI_TIMEOUT_ERROR = "Timeout при обращении к {provider} API"
AI_INVALID_RESPONSE_ERROR = "Некорректный формат ответа от {provider} API"
AI_EMPTY_RESPONSE_ERROR = "Пустой ответ от {provider} API"
AI_ALL_PROVIDERS_FAILED = "Все AI провайдеры недоступны: {error}"

# Сообщения об ошибках для пользователей
USER_NOT_FOUND_ERROR = "Пользователь не найден"
USER_CREATION_ERROR = "Ошибка при создании пользователя: {error}"
USER_UPDATE_ERROR = "Ошибка при обновлении пользователя: {error}"

# Сообщения об ошибках для диалогов
CONVERSATION_SAVE_ERROR = "❌ Не удалось сохранить диалог для пользователя {user_id}"
CONVERSATION_HISTORY_ERROR = "❌ Ошибка при получении истории: {error}"
