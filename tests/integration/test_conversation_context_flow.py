"""Интеграционные тесты для проверки потока работы с контекстом диалога."""

import asyncio
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_providers.base import (
    ConversationMessage,
    UserAIConversationContext,
)
from app.services.conversation import ConversationService
from app.services.conversation.conversation_history import (
    get_conversation_context_from_db,
    get_recent_conversation_history,
)


class TestConversationContextFlow:
    """Интеграционные тесты для проверки потока работы с контекстом диалога."""

    @pytest.fixture
    def conversation_service(self) -> ConversationService:
        """Фикстура для создания экземпляра сервиса."""
        service = ConversationService()
        # Инициализируем моки
        mock_cache_service = Mock()
        mock_cache_service.get_conversation_context = AsyncMock(return_value=None)
        mock_cache_service.set_user_activity = AsyncMock()

        # Мок для персистентности
        mock_persistence = Mock()
        mock_persistence.save_conversation_context = AsyncMock()
        mock_cache_service.conversation_persistence = mock_persistence

        service._cache_service = mock_cache_service
        service._initialized = True
        return service

    @pytest.mark.asyncio
    async def test_conversation_context_flow_multiple_users(
        self, conversation_service: ConversationService
    ) -> None:
        """Тест потока работы с контекстом диалога для нескольких пользователей."""
        # Создаем данные для двух пользователей
        user1_id = 123
        user2_id = 456

        # Симулируем диалоги для обоих пользователей
        for user_id in [user1_id, user2_id]:
            # Каждый пользователь отправляет 7 сообщений (больше лимита в 5)
            for i in range(7):
                await conversation_service.save_conversation_with_cache(
                    user_id=user_id,
                    user_message=f"User {user_id} message {i}",
                    ai_response=f"AI response to user {user_id} message {i}",
                    ai_model="test-model",
                    tokens_used=10 + i,
                    response_time=0.1 + i * 0.05,
                )

        # Проверяем, что метод сохранения контекста был вызван для каждого пользователя
        assert (
            conversation_service.cache_service.conversation_persistence.save_conversation_context.call_count
            == 14
        )

        # Проверяем, что для каждого пользователя были вызваны правильные аргументы
        calls = conversation_service.cache_service.conversation_persistence.save_conversation_context.call_args_list

        # Извлекаем вызовы для каждого пользователя
        user1_calls = [call for call in calls if call[0][0] == user1_id]
        user2_calls = [call for call in calls if call[0][0] == user2_id]

        # Проверяем, что каждый пользователь имеет 7 вызовов
        assert len(user1_calls) == 7
        assert len(user2_calls) == 7

        # Проверяем структуру данных в последних вызовах
        last_user1_call = user1_calls[-1]
        last_user2_call = user2_calls[-1]

        # Проверяем, что контекст содержит правильную структуру
        user1_context = last_user1_call[0][1]["context"]
        user2_context = last_user2_call[0][1]["context"]

        # Проверяем, что в контексте есть поля user_messages и ai_responses
        assert "user_messages" in user1_context
        assert "ai_responses" in user1_context
        assert "user_messages" in user2_context
        assert "ai_responses" in user2_context

        # Проверяем, что количество сообщений не превышает 5
        assert len(user1_context["user_messages"]) <= 5
        assert len(user1_context["ai_responses"]) <= 5
        assert len(user2_context["user_messages"]) <= 5
        assert len(user2_context["ai_responses"]) <= 5

    @pytest.mark.asyncio
    async def test_conversation_context_structure(
        self, conversation_service: ConversationService
    ) -> None:
        """Тест структуры контекста диалога."""
        user_id = 789

        # Сохраняем один диалог
        await conversation_service.save_conversation_with_cache(
            user_id=user_id,
            user_message="Hello AI",
            ai_response="Hello! How can I help you?",
            ai_model="test-model",
            tokens_used=15,
            response_time=0.2,
        )

        # Проверяем вызов сохранения контекста
        conversation_service.cache_service.conversation_persistence.save_conversation_context.assert_called()
        call_args = conversation_service.cache_service.conversation_persistence.save_conversation_context.call_args

        # Проверяем структуру переданных данных
        context_data = call_args[0][1]
        assert "conversation_data" in context_data
        assert "context" in context_data

        # Проверяем структуру контекста
        context = context_data["context"]
        assert "user_messages" in context
        assert "ai_responses" in context
        assert "last_interaction" in context
        assert "topics" in context
        assert "emotional_tone" in context

        # Проверяем, что user_messages и ai_responses являются списками
        assert isinstance(context["user_messages"], list)
        assert isinstance(context["ai_responses"], list)

        # Проверяем, что в списках есть сообщения
        assert len(context["user_messages"]) == 1
        assert len(context["ai_responses"]) == 1

        # Проверяем структуру отдельных сообщений
        user_message = context["user_messages"][0]
        ai_response = context["ai_responses"][0]

        assert "role" in user_message
        assert "content" in user_message
        assert "timestamp" in user_message
        assert user_message["role"] == "user"
        assert user_message["content"] == "Hello AI"

        assert "role" in ai_response
        assert "content" in ai_response
        assert "timestamp" in ai_response
        assert ai_response["role"] == "assistant"
        assert ai_response["content"] == "Hello! How can I help you?"
