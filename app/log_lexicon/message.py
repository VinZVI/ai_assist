"""
@file: message.py
@description: Лог-лексикон для обработчика текстовых сообщений
@created: 2025-10-07
"""

# Константы для лог-сообщений обработчика текстовых сообщений
MESSAGE_RECEIVED = "📥 Получено сообщение от @{username}: {chars} символов..."
MESSAGE_PROCESSING = "🔄 Обработка сообщения пользователя ID:{user_id}"
MESSAGE_USER_LIMIT_EXCEEDED = "🚫 Пользователь ID:{user_id} превысил лимит сообщений"
MESSAGE_AI_GENERATING = "🤖 Генерация ответа AI..."
MESSAGE_AI_RESPONSE = (
    "📤 Ответ от {provider}: {chars} символов, {tokens} токенов, {duration} сек"
)
MESSAGE_AI_RESPONSE_GENERATED = "✅ Ответ AI сгенерирован: {response}"
MESSAGE_CONVERSATION_SAVED = "💾 Диалог сохранен для пользователя ID:{user_id}"
MESSAGE_CONVERSATION_SAVE_ERROR = (
    "💥 Ошибка сохранения диалога для пользователя ID:{user_id}"
)
MESSAGE_SENT = (
    "✈️ Отправлено @{username}: {chars} символов, {tokens} токенов, {duration} сек"
)
MESSAGE_ERROR = "💥 Ошибка обработки сообщения от пользователя ID:{user_id}: {error}"
