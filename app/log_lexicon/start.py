"""
@file: log_lexicon/start.py
@description: Лог-сообщения для обработчика команды /start
@created: 2025-10-03
"""

# Лог-сообщения для обработчика /start
START_COMMAND_RECEIVED = "🚀 Команда /start от пользователя {user_info}"
START_COMMAND_PROCESSED = (
    "✅ Успешно обработана команда /start для пользователя {user_id}"
)
START_COMMAND_ERROR = (
    "💥 Ошибка в обработчике /start для пользователя {user_id}: {error}"
)
START_USER_INFO_UPDATED = "👤 Обновлена информация пользователя {user_id}"
START_NEW_USER_CREATED = "🆕 Создан новый пользователь: {user_id} (@{username})"
START_USER_CREATION_ERROR = (
    "❌ Ошибка целостности при создании пользователя {user_id}: {error}"
)
START_UNEXPECTED_ERROR = (
    "💥 Неожиданная ошибка при работе с пользователем {user_id}: {error}"
)
START_ERROR_SENDING_MESSAGE = "💥 Не удалось отправить сообщение об ошибке: {error}"
