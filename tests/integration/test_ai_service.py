"""
@file: test_ai_service.py
@description: Тесты для AI сервиса с DeepSeek API интеграцией
@dependencies: pytest, pytest-asyncio, httpx
@created: 2025-09-12
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

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

    def test_cache_init(self):
        """Тест инициализации кеша."""
        cache = ResponseCache(ttl_seconds=3600)
        assert cache._ttl == 3600
        assert cache._cache == {}

    def test_cache_key_generation(self):
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

    def test_cache_set_and_get(self):
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

    def test_cache_miss(self):
        """Тест промаха кеша."""
        cache = ResponseCache()
        messages = [ConversationMessage(role="user", content="Not cached")]

        result = cache.get(messages, "deepseek-chat")
        assert result is None

    def test_cache_ttl_expiration(self):
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

    def test_cache_clear(self):
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

    def test_message_creation(self):
        """Тест создания сообщения."""
        msg = ConversationMessage(
            role="user",
            content="Hello world",
            timestamp=datetime.now(),
        )

        assert msg.role == "user"
        assert msg.content == "Hello world"
        assert isinstance(msg.timestamp, datetime)

    def test_message_without_timestamp(self):
        """Тест создания сообщения без времени."""
        msg = ConversationMessage(role="assistant", content="Hi!")

        assert msg.role == "assistant"
        assert msg.content == "Hi!"
        assert msg.timestamp is None


class TestAIResponse:
    """Тесты для структуры ответа AI."""

    def test_response_creation(self):
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

    def test_response_default_cached(self):
        """Тест значения по умолчанию для cached."""
        response = AIResponse(
            content="Test",
            model="test-model",
            tokens_used=10,
            response_time=0.5,
        )

        assert response.cached is False


@pytest.mark.asyncio
class TestAIService:
    """Тесты для основного AI сервиса."""

    @pytest.fixture
    def ai_service(self):
        """Фикстура для создания AI сервиса."""
        return AIService()

    @pytest.fixture
    def mock_config(self):
        """Фикстура для мокирования конфигурации."""
        with patch("app.services.ai_service.get_config") as mock:
            config = MagicMock()
            config.deepseek.deepseek_api_key = "test-api-key"
            config.deepseek.deepseek_base_url = "https://api.test.com"
            config.deepseek.deepseek_model = "test-model"
            config.deepseek.deepseek_temperature = 0.7
            config.deepseek.deepseek_max_tokens = 1000
            config.deepseek.deepseek_timeout = 30
            config.redis.cache_ttl = 3600
            mock.return_value = config
            yield config

    async def test_service_initialization(self, ai_service, mock_config):
        """Тест инициализации AI сервиса."""
        assert ai_service._client is None
        assert ai_service._cache is not None
        assert ai_service._default_temperature == 0.7
        assert ai_service._default_max_tokens == 1000
        assert ai_service._timeout == 30

    async def test_get_client_creation(self, ai_service, mock_config):
        """Тест создания HTTP клиента."""
        client = await ai_service._get_client()

        assert client is not None
        assert isinstance(client, httpx.AsyncClient)
        assert ai_service._client is client

        # Проверяем, что повторный вызов возвращает тот же клиент
        client2 = await ai_service._get_client()
        assert client is client2

    async def test_client_close(self, ai_service, mock_config):
        """Тест закрытия HTTP клиента."""
        await ai_service._get_client()
        assert ai_service._client is not None

        await ai_service.close()
        assert ai_service._client is None

    def test_prepare_messages(self, ai_service):
        """Тест подготовки сообщений для API."""
        messages = [
            ConversationMessage(role="user", content="Hello"),
            ConversationMessage(role="assistant", content="Hi!"),
            ConversationMessage(role="user", content="How are you?"),
        ]

        prepared = ai_service._prepare_messages(messages)

        assert len(prepared) == 3
        assert prepared[0] == {"role": "user", "content": "Hello"}
        assert prepared[1] == {"role": "assistant", "content": "Hi!"}
        assert prepared[2] == {"role": "user", "content": "How are you?"}

    async def test_generate_response_validation(self, ai_service, mock_config):
        """Тест валидации параметров для генерации ответа."""
        # Тест пустого списка сообщений
        with pytest.raises(ValueError, match="Список сообщений не может быть пустым"):
            await ai_service.generate_response([])

        messages = [ConversationMessage(role="user", content="Test")]

        # Тест неправильной температуры
        with pytest.raises(ValueError, match="Temperature должна быть от 0.0 до 2.0"):
            await ai_service.generate_response(messages, temperature=3.0)

        # Тест неправильного количества токенов
        with pytest.raises(ValueError, match="max_tokens должно быть от 1 до 4000"):
            await ai_service.generate_response(messages, max_tokens=5000)

    @patch("app.services.ai_service.AIService._make_api_request")
    async def test_generate_response_success(
        self,
        mock_api_request,
        ai_service,
        mock_config,
    ):
        """Тест успешной генерации ответа."""
        # Мокируем ответ API
        mock_api_request.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Привет! Как дела?",
                    },
                },
            ],
            "usage": {
                "total_tokens": 25,
            },
        }

        messages = [ConversationMessage(role="user", content="Привет")]
        response = await ai_service.generate_response(messages, use_cache=False)

        assert isinstance(response, AIResponse)
        assert response.content == "Привет! Как дела?"
        assert response.tokens_used == 25
        assert response.model == "test-model"
        assert response.cached is False

    @patch("app.services.ai_service.AIService._make_api_request")
    async def test_generate_response_with_cache(
        self,
        mock_api_request,
        ai_service,
        mock_config,
    ):
        """Тест генерации ответа с кешированием."""
        # Мокируем ответ API для первого запроса
        mock_api_request.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Кешированный ответ",
                    },
                },
            ],
            "usage": {
                "total_tokens": 20,
            },
        }

        messages = [ConversationMessage(role="user", content="Тест кеша")]

        # Первый запрос - должен вызвать API
        response1 = await ai_service.generate_response(messages, use_cache=True)
        assert mock_api_request.call_count == 1
        assert response1.cached is False

        # Второй запрос - должен взять из кеша
        response2 = await ai_service.generate_response(messages, use_cache=True)
        assert mock_api_request.call_count == 1  # API не вызывался повторно
        assert response2.cached is True
        assert response2.content == "Кешированный ответ"

    async def test_generate_simple_response(self, ai_service, mock_config):
        """Тест упрощенного метода генерации ответа."""
        with patch.object(ai_service, "generate_response") as mock_generate:
            mock_generate.return_value = AIResponse(
                content="Простой ответ",
                model="test-model",
                tokens_used=10,
                response_time=0.5,
            )

            response = await ai_service.generate_simple_response("Привет")

            # Проверяем, что вызвался generate_response с правильными сообщениями
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args[1]
            messages = call_args["messages"]

            assert len(messages) == 2
            assert messages[0].role == "system"
            assert "эмпатичный AI-помощник" in messages[0].content
            assert messages[1].role == "user"
            assert messages[1].content == "Привет"

    def test_clear_cache(self, ai_service):
        """Тест очистки кеша сервиса."""
        # Добавляем что-то в кеш
        ai_service._cache._cache["test"] = {"data": "test"}

        # Очищаем кеш
        ai_service.clear_cache()

        # Проверяем, что кеш пуст
        assert ai_service._cache._cache == {}

    @patch("app.services.ai_service.AIService.generate_response")
    async def test_health_check_healthy(self, mock_generate, ai_service, mock_config):
        """Тест health check при работающем сервисе."""
        mock_generate.return_value = AIResponse(
            content="Health check response",
            model="test-model",
            tokens_used=5,
            response_time=0.3,
        )

        health = await ai_service.health_check()

        assert health["status"] == "healthy"
        assert health["model"] == "test-model"
        assert "response_time" in health
        assert health["cache_enabled"] is True

    @patch("app.services.ai_service.AIService.generate_response")
    async def test_health_check_unhealthy(self, mock_generate, ai_service, mock_config):
        """Тест health check при неработающем сервисе."""
        mock_generate.side_effect = APIConnectionError("Connection failed")

        health = await ai_service.health_check()

        assert health["status"] == "unhealthy"
        assert "error" in health
        assert "Connection failed" in health["error"]


class TestAIServiceErrors:
    """Тесты для обработки ошибок AI сервиса."""

    def test_error_hierarchy(self):
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

    async def test_get_ai_service_singleton(self):
        """Тест singleton behavior для get_ai_service."""
        # Очищаем глобальный экземпляр если есть
        await close_ai_service()

        service1 = get_ai_service()
        service2 = get_ai_service()

        assert service1 is service2  # Должен возвращать тот же экземпляр

        # Очищаем после теста
        await close_ai_service()

    async def test_close_ai_service(self):
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
    async def test_real_api_call(self):
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
