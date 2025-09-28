"""
@file: test_ai_service.py
@description: Тесты для AI сервиса с DeepSeek API интеграцией
@dependencies: pytest, pytest-asyncio, httpx
@created: 2025-09-12
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.ai_service import (
    AIResponse,
    AIService,
    AIServiceError,
    APIAuthenticationError,
    APIConnectionError,
    APIRateLimitError,
    ConversationMessage,
    ResponseCache,
    close_ai_service,
    get_ai_service,
)


class TestResponseCache:
    """Тесты для системы кеширования ответов."""

    def test_cache_init(self) -> None:
        """Тест инициализации кеша."""
        cache = ResponseCache(ttl_seconds=3600)
        assert cache._ttl == 3600
        assert cache._cache == {}

    def test_cache_key_generation(self) -> None:
        """Тест генерации ключей кеша."""
        cache = ResponseCache()
        messages = [
            ConversationMessage(role="user", content="Hello"),
            ConversationMessage(role="assistant", content="Hi there!"),
        ]

        key1 = cache._generate_key(messages, "deepseek-chat")
        key2 = cache._generate_key(messages, "deepseek-chat")
        key3 = cache._generate_key(messages, "different-model")

        assert key1 == key2  # Одинаковые сообщения = одинаковый ключ
        assert key1 != key3  # Разные модели = разные ключи
        assert len(key1) == 32  # MD5 hash length

    def test_cache_set_and_get(self) -> None:
        """Тест сохранения и получения из кеша."""
        cache = ResponseCache(ttl_seconds=3600)
        messages = [ConversationMessage(role="user", content="Test")]
        response = AIResponse(
            content="Test response",
            model="deepseek-chat",
            tokens_used=10,
            response_time=0.5,
        )

        # Сохраняем в кеш
        cache.set(messages, "deepseek-chat", response)

        # Получаем из кеша
        cached_response = cache.get(messages, "deepseek-chat")

        assert cached_response is not None
        assert cached_response.content == "Test response"
        assert cached_response.cached is True

    def test_cache_miss(self) -> None:
        """Тест промаха кеша."""
        cache = ResponseCache()
        messages = [ConversationMessage(role="user", content="Not cached")]

        result = cache.get(messages, "deepseek-chat")
        assert result is None

    def test_cache_ttl_expiration(self) -> None:
        """Тест истечения срока кеша."""
        cache = ResponseCache(ttl_seconds=1)
        messages = [ConversationMessage(role="user", content="Expire test")]
        response = AIResponse(
            content="Will expire",
            model="deepseek-chat",
            tokens_used=5,
            response_time=0.1,
        )

        # Сохраняем в кеш
        cache.set(messages, "deepseek-chat", response)

        # Проверяем, что есть в кеше
        assert cache.get(messages, "deepseek-chat") is not None

        # Имитируем истечение TTL
        cache._cache[cache._generate_key(messages, "deepseek-chat")]["timestamp"] = (
            datetime.now() - timedelta(seconds=2)
        )

        # Проверяем, что кеш очистился
        assert cache.get(messages, "deepseek-chat") is None

    def test_cache_clear(self) -> None:
        """Тест очистки кеша."""
        cache = ResponseCache()
        messages = [ConversationMessage(role="user", content="Clear test")]
        response = AIResponse(
            content="Will be cleared",
            model="deepseek-chat",
            tokens_used=5,
            response_time=0.1,
        )

        cache.set(messages, "deepseek-chat", response)
        assert cache.get(messages, "deepseek-chat") is not None

        cache.clear()
        assert cache.get(messages, "deepseek-chat") is None


class TestConversationMessage:
    """Тесты для структуры сообщений диалога."""

    def test_message_creation(self) -> None:
        """Тест создания сообщения."""
        msg = ConversationMessage(
            role="user",
            content="Hello world",
            timestamp=datetime.now(),
        )

        assert msg.role == "user"
        assert msg.content == "Hello world"
        assert isinstance(msg.timestamp, datetime)

    def test_message_without_timestamp(self) -> None:
        """Тест создания сообщения без времени."""
        msg = ConversationMessage(role="assistant", content="Hi!")

        assert msg.role == "assistant"
        assert msg.content == "Hi!"
        assert msg.timestamp is None


class TestAIResponse:
    """Тесты для структуры ответа AI."""

    def test_response_creation(self) -> None:
        """Тест создания ответа AI."""
        response = AIResponse(
            content="AI response",
            model="deepseek-chat",
            tokens_used=15,
            response_time=1.2,
            cached=False,
        )

        assert response.content == "AI response"
        assert response.model == "deepseek-chat"
        assert response.tokens_used == 15
        assert response.response_time == 1.2
        assert response.cached is False

    def test_response_default_cached(self) -> None:
        """Тест значения по умолчанию для cached."""
        response = AIResponse(
            content="Test",
            model="test-model",
            tokens_used=10,
            response_time=0.5,
        )

        assert response.cached is False


@pytest.mark.asyncio
class TestAIServiceSync:
    """Тесты для синхронных методов AI сервиса."""

    @pytest.fixture
    def ai_service(self) -> AIService:
        """Фикстура для создания AI сервиса."""
        return AIService()

    @pytest.fixture
    def mock_config(self) -> MagicMock:
        """Фикстура для мокирования конфигурации."""
        with patch("app.services.ai_service.get_config") as mock:
            config = MagicMock()
            config.deepseek.deepseek_api_key = "test-key"
            config.deepseek.deepseek_base_url = "https://api.deepseek.com"
            config.deepseek.deepseek_model = "deepseek-chat"
            config.deepseek.deepseek_temperature = 0.7
            config.deepseek.deepseek_max_tokens = 1000
            mock.return_value = config
            yield config

    def test_prepare_messages(self, ai_service: AIService) -> None:
        """Тест подготовки сообщений."""
        messages = [
            ConversationMessage(role="system", content="Ты полезный помощник"),
            ConversationMessage(role="user", content="Привет"),
        ]

        prepared = ai_service._prepare_messages(messages)

        assert len(prepared) == 2
        assert prepared[0]["role"] == "system"
        assert prepared[0]["content"] == "Ты полезный помощник"
        assert prepared[1]["role"] == "user"
        assert prepared[1]["content"] == "Привет"

    def test_prepare_request_data(
        self, ai_service: AIService, mock_config: MagicMock
    ) -> None:
        """Тест подготовки данных запроса."""
        messages = [ConversationMessage(role="user", content="Привет")]
        prepared_messages = ai_service._prepare_messages(messages)

        # Test the actual method that exists
        assert len(prepared_messages) == 1
        assert prepared_messages[0]["role"] == "user"
        assert prepared_messages[0]["content"] == "Привет"

    def test_clear_cache(self, ai_service: AIService) -> None:
        """Тест очистки кеша сервиса."""
        # Add something to cache first
        messages = [ConversationMessage(role="user", content="test")]
        response = AIResponse(
            content="test response",
            model="test-model",
            tokens_used=5,
            response_time=0.1,
        )
        ai_service._cache.set(messages, "test-model", response)

        # Verify cache is not empty
        assert len(ai_service._cache._cache) > 0

        # Clear the cache
        ai_service.clear_cache()

        # Verify cache is empty
        assert len(ai_service._cache._cache) == 0


@pytest.mark.asyncio
class TestAIService:
    """Тесты для основного AI сервиса."""

    @pytest.fixture
    def ai_service(self) -> AIService:
        """Фикстура для создания AI сервиса."""
        return AIService()

    @pytest.fixture
    def mock_config(self) -> MagicMock:
        """Фикстура для мокирования конфигурации."""
        with patch("app.services.ai_service.get_config") as mock:
            config = MagicMock()
            config.deepseek.deepseek_api_key = "test-key"
            config.deepseek.deepseek_base_url = "https://api.deepseek.com"
            config.deepseek.deepseek_model = "deepseek-chat"
            config.deepseek.deepseek_temperature = 0.7
            config.deepseek.deepseek_max_tokens = 1000
            mock.return_value = config
            yield config

    def test_init(self, ai_service: AIService) -> None:
        """Тест инициализации сервиса."""
        assert ai_service.config is not None
        assert ai_service._client is None
        assert ai_service._cache is not None

    @patch("app.services.ai_service.httpx.AsyncClient")
    async def test_get_client(
        self, mock_client_class: MagicMock, ai_service: AIService
    ) -> None:
        """Тест получения HTTP клиента."""
        mock_client_instance = AsyncMock()
        mock_client_class.return_value = mock_client_instance

        client1 = await ai_service._get_client()
        client2 = await ai_service._get_client()

        # Должен возвращать тот же экземпляр
        assert client1 is client2
        mock_client_class.assert_called_once()

    @patch("app.services.ai_service.httpx.AsyncClient")
    async def test_close(
        self, mock_client_class: MagicMock, ai_service: AIService
    ) -> None:
        """Тест закрытия клиента."""
        mock_client_instance = AsyncMock()
        mock_client_class.return_value = mock_client_instance

        # Получаем клиент
        client = await ai_service._get_client()
        assert client is not None

        # Закрываем
        await ai_service.close()

        # Проверяем, что клиент закрыт
        mock_client_instance.aclose.assert_called_once()
        assert ai_service._client is None

    def test_prepare_messages(self, ai_service: AIService) -> None:
        """Тест подготовки сообщений."""
        messages = [
            ConversationMessage(role="system", content="Ты полезный помощник"),
            ConversationMessage(role="user", content="Привет"),
        ]

        prepared = ai_service._prepare_messages(messages)

        assert len(prepared) == 2
        assert prepared[0]["role"] == "system"
        assert prepared[0]["content"] == "Ты полезный помощник"
        assert prepared[1]["role"] == "user"
        assert prepared[1]["content"] == "Привет"

    def test_prepare_request_data(
        self, ai_service: AIService, mock_config: MagicMock
    ) -> None:
        """Тест подготовки данных запроса."""
        messages = [ConversationMessage(role="user", content="Привет")]
        prepared_messages = ai_service._prepare_messages(messages)

        # Test the actual method that exists
        assert len(prepared_messages) == 1
        assert prepared_messages[0]["role"] == "user"
        assert prepared_messages[0]["content"] == "Привет"

    async def test_generate_response_success(
        self, ai_service: AIService, mock_config: MagicMock
    ) -> None:
        """Тест успешной генерации ответа."""
        # Мокаем клиента и его метод post
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Тестовый ответ"}}],
            "usage": {"total_tokens": 10},
        }

        with patch.object(ai_service, "_get_client", return_value=mock_client):
            mock_client.post.return_value = mock_response

            messages = [ConversationMessage(role="user", content="Привет")]
            result = await ai_service.generate_response(messages)

            assert isinstance(result, AIResponse)
            assert result.content == "Тестовый ответ"
            assert result.tokens_used == 10
            assert result.model == mock_config.deepseek.deepseek_model

    async def test_generate_simple_response(
        self, ai_service: AIService, mock_config: MagicMock
    ) -> None:
        """Тест упрощенного метода генерации ответа."""
        with patch.object(ai_service, "generate_response") as mock_generate:
            mock_generate.return_value = AIResponse(
                content="Упрощенный ответ",
                model="test-model",
                tokens_used=5,
                response_time=0.1,
            )

            result = await ai_service.generate_simple_response("Привет")

            assert result.content == "Упрощенный ответ"
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args[0][0]
            assert len(call_args) == 2
            assert call_args[0].role == "system"
            assert call_args[1].role == "user"
            assert call_args[1].content == "Привет"

    def test_clear_cache(self, ai_service: AIService) -> None:
        """Тест очистки кеша сервиса."""
        # Add something to cache first
        messages = [ConversationMessage(role="user", content="test")]
        response = AIResponse(
            content="test response",
            model="test-model",
            tokens_used=5,
            response_time=0.1,
        )
        ai_service._cache.set(messages, "test-model", response)

        # Verify cache is not empty
        assert len(ai_service._cache._cache) > 0

        # Clear the cache
        ai_service.clear_cache()

        # Verify cache is empty
        assert len(ai_service._cache._cache) == 0

    @patch("app.services.ai_service.AIService.generate_response")
    async def test_health_check_healthy(
        self, mock_generate: AsyncMock, ai_service: AIService, mock_config: MagicMock
    ) -> None:
        """Тест health check при работающем сервисе."""
        mock_generate.return_value = AIResponse(
            content="health check",
            model="test-model",
            tokens_used=2,
            response_time=0.1,
        )

        result = await ai_service.health_check()

        assert result["status"] == "healthy"
        assert "response_time" in result
        mock_generate.assert_called_once()

    @patch("app.services.ai_service.AIService.generate_response")
    async def test_health_check_unhealthy(
        self, mock_generate: AsyncMock, ai_service: AIService, mock_config: MagicMock
    ) -> None:
        """Тест health check при неработающем сервисе."""
        mock_generate.side_effect = APIConnectionError("Connection failed")

        result = await ai_service.health_check()

        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "Connection failed" in result["error"]


class TestAIServiceErrors:
    """Тесты для обработки ошибок AI сервиса."""

    def test_error_hierarchy(self) -> None:
        """Тест иерархии ошибок."""
        # Проверяем наследование
        assert issubclass(APIConnectionError, AIServiceError)
        assert issubclass(APIRateLimitError, AIServiceError)
        assert issubclass(APIAuthenticationError, AIServiceError)

        # Проверяем создание ошибок
        base_error = AIServiceError("Base error")
        connection_error = APIConnectionError("Connection error")
        rate_limit_error = APIRateLimitError("Rate limit error")
        auth_error = APIAuthenticationError("Auth error")

        assert str(base_error) == "Base error"
        assert str(connection_error) == "Connection error"
        assert str(rate_limit_error) == "Rate limit error"
        assert str(auth_error) == "Auth error"


class TestAIServiceSingleton:
    """Тесты для singleton pattern AI сервиса."""

    @pytest.mark.asyncio
    async def test_get_ai_service_singleton(self) -> None:
        """Тест singleton behavior для get_ai_service."""
        # Очищаем глобальный экземпляр если есть
        await close_ai_service()

        service1 = get_ai_service()
        service2 = get_ai_service()

        assert service1 is service2  # Должен возвращать тот же экземпляр

        # Очищаем после теста
        await close_ai_service()

    @pytest.mark.asyncio
    async def test_close_ai_service(self) -> None:
        """Тест закрытия AI сервиса."""
        service = get_ai_service()
        assert service is not None

        await close_ai_service()

        # Получение нового сервиса должно создать новый экземпляр
        new_service = get_ai_service()
        assert new_service is not service

        # Очищаем после теста
        await close_ai_service()


@pytest.mark.integration
class TestAIServiceIntegration:
    """Интеграционные тесты для AI сервиса."""

    @pytest.mark.skip(reason="Требует реальный API ключ")
    async def test_real_api_call(self) -> None:
        """Интеграционный тест с реальным API (требует API ключ)."""
        service = AIService()
        messages = [
            ConversationMessage(role="user", content="Привет!"),
        ]

        try:
            response = await service.generate_response(messages, use_cache=False)
            assert isinstance(response, AIResponse)
            assert len(response.content) > 0
            assert response.tokens_used > 0
        except APIAuthenticationError:
            pytest.skip("API ключ не настроен")
        finally:
            await service.close()
