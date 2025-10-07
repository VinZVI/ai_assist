"""
@file: start.py
@description: Лог-лексикон для обработчика команды /start
@created: 2025-10-07
"""

# Константы для лог-сообщений обработчика /start
START_COMMAND_RECEIVED = "📥 Получена команда /start от пользователя ID:{user_id}"
START_NEW_USER_CREATED = "🆕 Создан новый пользователь ID:{user_id} (@{username})"
START_USER_INFO_UPDATED = "🔄 Обновлена информация пользователя ID:{user_id}"
START_COMMAND_PROCESSED = "✅ Команда /start обработана для пользователя ID:{user_id}"
START_COMMAND_ERROR = (
    "💥 Ошибка обработки /start для пользователя ID:{user_id}: {error}"
)
START_USER_CREATION_ERROR = "💥 Ошибка создания пользователя ID:{user_id}: {error}"
START_UNEXPECTED_ERROR = "💥 Неожиданная ошибка для пользователя ID:{user_id}: {error}"
START_ERROR_SENDING_MESSAGE = "💥 Ошибка отправки сообщения: {error}"
