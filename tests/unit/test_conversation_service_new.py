"""
Тесты для нового сервиса диалогов.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, UTC

from app.services.conversation_service_new import ConversationService


class TestConversationServiceNew:
    """Тесты для нового сервиса диалогов."""

    @pytest.fixture
    def conversation_service(self):
        """Фикстура для создания экземпляра сервиса."""
        service = ConversationService()
        return service

    @pytest.mark.asyncio
    async def test_initialize(self, conversation_service):
        """Тест инициализации сервиса."""
        with patch("app.services.conversation_service_new.container") as mock_container:
            # Создаем mock для cache_service
            mock_cache_service = Mock()
            mock_container.get.return_value = mock_cache_service

            # Вызываем тестируемый метод
            await conversation_service.initialize()

            # Проверяем, что флаг инициализации установлен
            assert conversation_service._initialized is True

            # Проверяем, что cache_service был получен из контейнера
            mock_container.get.assert_called_once_with("cache_service")

    def test_cache_service_property(self, conversation_service):
        """Тест свойства cache_service."""
        # Создаем mock для cache_service
        mock_cache_service = Mock()

        # Устанавливаем его напрямую как приватное свойство
        conversation_service._cache_service = mock_cache_service

        # Получаем cache_service через свойство
        cache_service = conversation_service.cache_service

        # Проверяем, что возвращается установленный mock
        assert cache_service is mock_cache_service

    @pytest.mark.asyncio
    async def test_save_conversation_with_cache_success(self, conversation_service):
        """Тест успешного сохранения диалога в кэш."""
        # Создаем mock для cache_service
        mock_cache_service = Mock()
        mock_persistence = Mock()
        mock_cache_service.conversation_persistence = mock_persistence
        mock_persistence.save_conversation_context = AsyncMock()
        mock_cache_service.set_user_activity = AsyncMock()

        # Устанавливаем mock как приватное свойство
        conversation_service._cache_service = mock_cache_service

        with patch(
            "app.utils.validators.InputValidator.validate_message_length"
        ) as mock_validate:
            # Настраиваем mock для успешной валидации
            mock_validate.return_value = (True, "")

            # Вызываем тестируемый метод
            result = await conversation_service.save_conversation_with_cache(
                user_id=123,
                user_message="Hello",
                ai_response="Hi there!",
                ai_model="test-model",
                tokens_used=10,
                response_time=0.5,
            )

            # Проверяем результат
            assert result is True

            # Проверяем, что метод сохранения был вызван с правильными аргументами
            mock_persistence.save_conversation_context.assert_called_once()
            call_args = mock_persistence.save_conversation_context.call_args
            assert call_args[0][0] == 123  # user_id
            assert "conversation_data" in call_args[0][1]

            conversation_data = call_args[0][1]["conversation_data"]
            assert conversation_data["user_message"] == "Hello"
            assert conversation_data["ai_response"] == "Hi there!"
            assert conversation_data["ai_model"] == "test-model"
            assert conversation_data["tokens_used"] == 10
            assert conversation_data["response_time"] == 0.5
            assert "timestamp" in conversation_data

            # Проверяем, что метод обновления активности был вызван
            mock_cache_service.set_user_activity.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_save_conversation_with_cache_validation_failure(
        self, conversation_service
    ):
        """Тест сохранения диалога при неудачной валидации."""
        with patch(
            "app.utils.validators.InputValidator.validate_message_length"
        ) as mock_validate:
            # Настраиваем mock для неудачной валидации
            mock_validate.return_value = (False, "Message too long")

            # Создаем mock для cache_service
            mock_cache_service = Mock()
            conversation_service._cache_service = mock_cache_service

            # Вызываем тестируемый метод
            result = await conversation_service.save_conversation_with_cache(
                user_id=123,
                user_message="A" * 10000,  # Очень длинное сообщение
                ai_response="Hi there!",
                ai_model="test-model",
                tokens_used=10,
                response_time=0.5,
            )

            # Проверяем результат
            assert result is False

    @pytest.mark.asyncio
    async def test_save_conversation_with_cache_exception(self, conversation_service):
        """Тест сохранения диалога при возникновении исключения."""
        with patch(
            "app.utils.validators.InputValidator.validate_message_length"
        ) as mock_validate:
            # Настраиваем mock для успешной валидации
            mock_validate.return_value = (True, "")

            # Создаем mock для cache_service
            mock_cache_service = Mock()
            mock_persistence = Mock()
            mock_cache_service.conversation_persistence = mock_persistence
            mock_persistence.save_conversation_context = AsyncMock(
                side_effect=Exception("Test error")
            )
            mock_cache_service.set_user_activity = AsyncMock()

            # Устанавливаем mock как приватное свойство
            conversation_service._cache_service = mock_cache_service

            # Вызываем тестируемый метод
            result = await conversation_service.save_conversation_with_cache(
                user_id=123,
                user_message="Hello",
                ai_response="Hi there!",
                ai_model="test-model",
                tokens_used=10,
                response_time=0.5,
            )

            # Проверяем результат
            assert result is False
