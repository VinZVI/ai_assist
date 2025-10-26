"""Тесты для UserAIConversationContext."""

from datetime import UTC, datetime

import pytest

from app.services.ai_providers.base import (
    ConversationMessage,
    UserAIConversationContext,
)


class TestUserAIConversationContext:
    """Тесты для UserAIConversationContext."""

    def test_initialization(self) -> None:
        """Тест инициализации контекста."""
        context = UserAIConversationContext(
            user_messages=[],
            ai_responses=[],
            last_interaction=None,
            topics=[],
            emotional_tone="neutral",
        )

        assert context.user_messages == []
        assert context.ai_responses == []
        assert context.last_interaction is None
        assert context.topics == []
        assert context.emotional_tone == "neutral"

    def test_add_user_message_limit(self) -> None:
        """Тест ограничения количества пользовательских сообщений до 5."""
        context = UserAIConversationContext(
            user_messages=[],
            ai_responses=[],
            last_interaction=None,
            topics=[],
            emotional_tone="neutral",
        )

        # Добавляем 7 сообщений пользователя
        for i in range(7):
            message = ConversationMessage(
                role="user", content=f"User message {i}", timestamp=datetime.now(UTC)
            )
            context.add_user_message(message)

        # Проверяем, что осталось только 5 последних сообщений
        assert len(context.user_messages) == 5
        assert context.user_messages[0].content == "User message 2"
        assert context.user_messages[4].content == "User message 6"

        # Проверяем, что last_interaction обновлен
        assert context.last_interaction == context.user_messages[4].timestamp

    def test_add_ai_response_limit(self) -> None:
        """Тест ограничения количества ответов ИИ до 5."""
        context = UserAIConversationContext(
            user_messages=[],
            ai_responses=[],
            last_interaction=None,
            topics=[],
            emotional_tone="neutral",
        )

        # Добавляем 7 ответов ИИ
        for i in range(7):
            response = ConversationMessage(
                role="assistant",
                content=f"AI response {i}",
                timestamp=datetime.now(UTC),
            )
            context.add_ai_response(response)

        # Проверяем, что осталось только 5 последних ответов
        assert len(context.ai_responses) == 5
        assert context.ai_responses[0].content == "AI response 2"
        assert context.ai_responses[4].content == "AI response 6"

        # Проверяем, что last_interaction обновлен
        assert context.last_interaction == context.ai_responses[4].timestamp

    def test_get_combined_history(self) -> None:
        """Тест получения объединенной истории сообщений."""
        context = UserAIConversationContext(
            user_messages=[],
            ai_responses=[],
            last_interaction=None,
            topics=[],
            emotional_tone="neutral",
        )

        # Добавляем сообщения пользователя и ответы ИИ с разными временными метками
        base_time = datetime.now(UTC)
        user_messages = [
            ConversationMessage("user", "User 1", base_time.replace(second=1)),
            ConversationMessage("user", "User 2", base_time.replace(second=3)),
            ConversationMessage("user", "User 3", base_time.replace(second=5)),
        ]

        ai_responses = [
            ConversationMessage("assistant", "AI 1", base_time.replace(second=2)),
            ConversationMessage("assistant", "AI 2", base_time.replace(second=4)),
            ConversationMessage("assistant", "AI 3", base_time.replace(second=6)),
        ]

        # Добавляем в контекст
        for msg in user_messages:
            context.add_user_message(msg)
        for resp in ai_responses:
            context.add_ai_response(resp)

        # Получаем объединенную историю
        history = context.get_combined_history()

        # Проверяем, что история отсортирована по времени
        assert len(history) == 6
        assert history[0].content == "User 1"
        assert history[1].content == "AI 1"
        assert history[2].content == "User 2"
        assert history[3].content == "AI 2"
        assert history[4].content == "User 3"
        assert history[5].content == "AI 3"

    def test_to_dict_and_from_dict(self) -> None:
        """Тест сериализации и десериализации контекста."""
        # Создаем контекст с данными
        base_time = datetime.now(UTC)
        user_messages = [
            ConversationMessage("user", "Hello", base_time.replace(second=1)),
        ]
        ai_responses = [
            ConversationMessage("assistant", "Hi there!", base_time.replace(second=2)),
        ]

        original_context = UserAIConversationContext(
            user_messages=user_messages,
            ai_responses=ai_responses,
            last_interaction=base_time.replace(second=2),
            topics=["greeting"],
            emotional_tone="positive",
        )

        # Преобразуем в словарь
        context_dict = original_context.to_dict()

        # Создаем новый контекст из словаря
        restored_context = UserAIConversationContext.from_dict(context_dict)

        # Проверяем, что данные совпадают
        assert len(restored_context.user_messages) == 1
        assert restored_context.user_messages[0].role == "user"
        assert restored_context.user_messages[0].content == "Hello"

        assert len(restored_context.ai_responses) == 1
        assert restored_context.ai_responses[0].role == "assistant"
        assert restored_context.ai_responses[0].content == "Hi there!"

        assert restored_context.last_interaction == base_time.replace(second=2)
        assert restored_context.topics == ["greeting"]
        assert restored_context.emotional_tone == "positive"
