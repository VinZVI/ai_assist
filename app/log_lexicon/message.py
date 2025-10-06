"""
@file: log_lexicon/message.py
@description: Лог-сообщения для обработчика текстовых сообщений
@created: 2025-10-03
"""

# Лог-сообщения для обработчика сообщений
MESSAGE_RECEIVED = "📥 Получено сообщение от пользователя {username}: {chars} символов"
MESSAGE_USER_LIMIT_EXCEEDED = "⚠️ Пользователь {user_id} превысил лимит сообщений"
MESSAGE_PROCESSING = "⚙️ Обработка сообщения пользователя {user_id}"
MESSAGE_AI_RESPONSE = (
    "🤖 AI ответ получен от {provider}: {chars} символов, {tokens} токенов, {duration}s"
)
MESSAGE_SENT = (
    "✅ Ответ отправлен пользователю {username}: {chars} символов, "
    "{tokens} токенов, {duration}s"
)
MESSAGE_ERROR = "❌ Ошибка при обработке сообщения от пользователя {user_id}: {error}"
MESSAGE_CONVERSATION_SAVED = "💾 Диалог сохранен для пользователя {user_id}"
MESSAGE_CONVERSATION_SAVE_ERROR = "💥 Ошибка при сохранении диалога: {error}"
MESSAGE_AI_GENERATING = "Генерируем ответ от AI"
MESSAGE_AI_RESPONSE_GENERATED = "Ответ от AI сгенерирован: {response}"
