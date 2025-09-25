"""
@file: test_openrouter_provider.py
@description: Тесты для OpenRouter AI провайдера
@dependencies: pytest, pytest-asyncio, unittest.mock, httpx
@created: 2025-09-20
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.ai_providers.openrouter import OpenRouterProvider
from app.services.ai_providers.base import (
    ConversationMessage, 
    AIResponse,
    APIConnectionError,
    APIRateLimitError,
    APIAuthenticationError,
    APIQuotaExceededError
)


@pytest.mark.ai_providers
@pytest.mark.integration
class TestOpenRouterProviderInitialization:
    """Тесты инициализации OpenRouter провайдера."""
    
    def test_provider_initialization(self, mock_config):
        """Тест инициализации провайдера."""
        provider = OpenRouterProvider()
        
        assert provider.name == "openrouter"
        assert provider.provider_name == "openrouter"
        assert hasattr(provider, '_client')
    
    def test_provider_configuration_check(self, mock_config):
        """Тест проверки конфигурации провайдера."""
        provider = OpenRouterProvider()
        
        assert provider.is_configured() is True
        
        # Тест с пустым API ключом
        with patch('app.services.ai_providers.openrouter.get_config') as mock_get_config:
            # Мок конфига с пустым ключом
            mock_empty_config = MagicMock()
            mock_empty_config.openrouter.openrouter_api_key = ""
            mock_empty_config.openrouter.is_configured.return_value = False
            mock_get_config.return_value = mock_empty_config
            
            provider_unconfigured = OpenRouterProvider()
            assert provider_unconfigured.is_configured() is False
    
    def test_provider_availability_check(self, mock_config):
        """Тест проверки доступности провайдера."""
        provider = OpenRouterProvider()
        
        # По умолчанию провайдер считается доступным если настроен
        # Note: is_available() is async, но в простых тестах можно проверить is_configured()
        assert provider.is_configured() is True


@pytest.mark.ai_providers
@pytest.mark.integration
class TestOpenRouterAPIRequests:
    """Тесты HTTP запросов к OpenRouter API."""
    
    @pytest.fixture
    def provider(self, mock_config):
        """Провайдер для тестов."""
        return OpenRouterProvider()
    
    @pytest.fixture
    def sample_messages(self):
        """Пример сообщений для тестов."""
        return [
            ConversationMessage(role="system", content="Ты полезный AI помощник."),
            ConversationMessage(role="user", content="Привет! Как дела?")
        ]
    
    @pytest.mark.asyncio
    async def test_successful_api_request(self, provider, sample_messages):
        """Тест успешного API запроса."""
        # Мокаем HTTP ответ
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "anthropic/claude-3-haiku",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Привет! У меня всё отлично, спасибо!"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 15,
                "total_tokens": 35
            }
        }
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            response = await provider.generate_response(sample_messages)
            
            assert isinstance(response, AIResponse)
            assert response.content == "Привет! У меня всё отлично, спасибо!"
            assert response.model == "anthropic/claude-3-haiku"
            assert response.provider == "openrouter"
            assert response.tokens_used == 35
            assert response.cached is False
    
    @pytest.mark.asyncio
    async def test_api_request_with_parameters(self, provider, sample_messages):
        """Тест API запроса с дополнительными параметрами."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Ответ с параметрами"}}],
            "usage": {"total_tokens": 25},
            "model": "anthropic/claude-3-haiku"
        }
        
        with patch('httpx.AsyncClient.post', return_value=mock_response) as mock_post:
            await provider.generate_response(
                sample_messages,
                temperature=0.8,
                max_tokens=500
            )
            
            # Проверяем что параметры переданы в запрос
            call_kwargs = mock_post.call_args[1]
            request_data = call_kwargs['json']
            
            assert request_data['temperature'] == 0.8
            assert request_data['max_tokens'] == 500
    
    @pytest.mark.asyncio
    async def test_http_headers(self, provider, sample_messages):
        """Тест правильных HTTP заголовков."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Тест заголовков"}}],
            "usage": {"total_tokens": 10},
            "model": "test-model"
        }
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            with patch('httpx.AsyncClient.__init__', return_value=None) as mock_client_init:
                # Принудительно очищаем клиент
                provider._client = None
                
                await provider.generate_response(sample_messages)
                
                # Проверяем заголовки при создании клиента
                mock_client_init.assert_called_once()
                call_kwargs = mock_client_init.call_args[1]
                headers = call_kwargs.get('headers', {})
                
                assert "Authorization" in headers
                assert headers["Authorization"].startswith("Bearer ")
                assert headers["Content-Type"] == "application/json"
                assert "HTTP-Referer" in headers
                assert "X-Title" in headers


@pytest.mark.ai_providers
@pytest.mark.integration
class TestOpenRouterErrorHandling:
    """Тесты обработки ошибок OpenRouter API."""
    
    @pytest.fixture
    def provider(self, mock_config):
        """Провайдер для тестов ошибок."""
        return OpenRouterProvider()
    
    @pytest.fixture  
    def sample_messages(self):
        """Сообщения для тестов ошибок."""
        return [ConversationMessage(role="user", content="Тест ошибок")]
    
    @pytest.mark.asyncio
    async def test_authentication_error(self, provider, sample_messages):
        """Тест ошибки аутентификации (401)."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid API key",
                "type": "authentication_error"
            }
        }
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            with pytest.raises(APIAuthenticationError, match="Неверный API ключ OpenRouter"):
                await provider.generate_response(sample_messages)
    
    @pytest.mark.asyncio
    async def test_quota_exceeded_error(self, provider, sample_messages):
        """Тест ошибки превышения квоты (402)."""
        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_response.json.return_value = {
            "error": {
                "message": "Insufficient credits",
                "type": "insufficient_quota"
            }
        }
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            with pytest.raises(APIQuotaExceededError, match="Недостаточно средств на счете OpenRouter API"):
                await provider.generate_response(sample_messages)
    
    @pytest.mark.asyncio
    async def test_rate_limit_error(self, provider, sample_messages):
        """Тест ошибки превышения лимита (429)."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "error": {
                "message": "Rate limit exceeded", 
                "type": "rate_limit_exceeded"
            }
        }
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            with pytest.raises(APIRateLimitError, match="Превышен лимит запросов к OpenRouter API"):
                await provider.generate_response(sample_messages)
    
    @pytest.mark.asyncio
    async def test_server_error(self, provider, sample_messages):
        """Тест серверной ошибки (5xx)."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            with pytest.raises(APIConnectionError, match="Ошибка сервера OpenRouter: 500"):
                await provider.generate_response(sample_messages)
    
    @pytest.mark.asyncio
    async def test_connection_error(self, provider, sample_messages):
        """Тест ошибки подключения."""
        with patch('httpx.AsyncClient.post', side_effect=httpx.ConnectError("Connection failed")):
            with pytest.raises(APIConnectionError, match="Не удалось подключиться к OpenRouter API"):
                await provider.generate_response(sample_messages)
    
    @pytest.mark.asyncio
    async def test_timeout_error(self, provider, sample_messages):
        """Тест ошибки таймаута."""
        with patch('httpx.AsyncClient.post', side_effect=httpx.TimeoutException("Request timed out")):
            with pytest.raises(APIConnectionError, match="Timeout при обращении к OpenRouter API"):
                await provider.generate_response(sample_messages)
    
    @pytest.mark.asyncio
    async def test_invalid_json_response(self, provider, sample_messages):
        """Тест некорректного JSON ответа."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Invalid response"
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            with pytest.raises(APIConnectionError, match="Invalid JSON"):
                await provider.generate_response(sample_messages)


@pytest.mark.ai_providers
@pytest.mark.integration
class TestOpenRouterResponseParsing:
    """Тесты парсинга ответов OpenRouter API."""
    
    @pytest.fixture
    def provider(self, mock_config):
        """Провайдер для тестов парсинга."""
        return OpenRouterProvider()
    
    @pytest.mark.asyncio
    async def test_minimal_response_parsing(self, provider):
        """Тест парсинга минимального ответа."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Минимальный ответ"}}]
        }
        
        messages = [ConversationMessage(role="user", content="Тест")]
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            response = await provider.generate_response(messages)
            
            assert response.content == "Минимальный ответ"
            assert response.tokens_used == 2  # len("Минимальный ответ".split()) * 1.3 ≈ 2
            assert response.model == "anthropic/claude-3-haiku"  # From config
    
    @pytest.mark.asyncio
    async def test_empty_content_handling(self, provider):
        """Тест обработки пустого контента."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": ""}}]
        }
        
        messages = [ConversationMessage(role="user", content="Тест")]
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            with pytest.raises(APIConnectionError, match="Пустой ответ от OpenRouter API"):
                await provider.generate_response(messages)
    
    @pytest.mark.asyncio
    async def test_missing_choices_handling(self, provider):
        """Тест обработки отсутствующих choices."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "test"}  # Нет choices
        
        messages = [ConversationMessage(role="user", content="Тест")]
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            with pytest.raises(APIConnectionError, match="Некорректный формат ответа от OpenRouter API"):
                await provider.generate_response(messages)


@pytest.mark.ai_providers
@pytest.mark.unit
class TestOpenRouterHelperMethods:
    """Тесты вспомогательных методов OpenRouter провайдера."""
    
    # def test_format_messages(self, mock_config):
    #     """Тест форматирования сообщений для API."""
    #     provider = OpenRouterProvider()
    #     
    #     messages = [
    #         ConversationMessage(role="system", content="Ты помощник"),
    #         ConversationMessage(role="user", content="Привет"),
    #         ConversationMessage(role="assistant", content="Привет!")
    #     ]
    #     
    #     formatted = provider._format_messages(messages)
    #     
    #     assert len(formatted) == 3
    #     assert formatted[0]["role"] == "system"
    #     assert formatted[0]["content"] == "Ты помощник"
    #     assert formatted[1]["role"] == "user"
    #     assert formatted[2]["role"] == "assistant"
    
    # def test_prepare_request_data(self, mock_config):
    #     """Тест подготовки данных запроса."""
    #     provider = OpenRouterProvider()
    #     
    #     messages = [ConversationMessage(role="user", content="Тест")]
    #     
    #     request_data = provider._prepare_request_data(
    #         messages, 
    #         temperature=0.8,
    #         max_tokens=100
    #     )
    #     
    #     assert request_data["model"] == mock_config.openrouter.openrouter_model
    #     assert request_data["temperature"] == 0.8
    #     assert request_data["max_tokens"] == 100
    #     assert "messages" in request_data
    #     assert len(request_data["messages"]) == 1


@pytest.mark.ai_providers
@pytest.mark.integration
class TestOpenRouterProviderLifecycle:
    """Тесты жизненного цикла OpenRouter провайдера."""
    
    @pytest.mark.asyncio
    async def test_provider_close(self, mock_config):
        """Тест закрытия провайдера."""
        provider = OpenRouterProvider()
        
        # Создаем мок клиента
        mock_client = AsyncMock()
        provider._client = mock_client
        
        await provider.close()
        
        mock_client.aclose.assert_called_once()
        assert provider._client is None
    
    # @pytest.mark.asyncio
    # async def test_context_manager_usage(self, mock_config):
    #     """Тест использования провайдера как context manager."""
    #     async with OpenRouterProvider(mock_config.openrouter) as provider:
    #         assert provider is not None
    #         assert hasattr(provider, '_config')
    #     
    #     # После выхода из контекста провайдер должен быть закрыт
    #     assert provider._client is None


@pytest.mark.ai_providers
@pytest.mark.slow
@pytest.mark.integration  
class TestOpenRouterRealAPI:
    """Тесты с реальным OpenRouter API (медленные)."""
    
    @pytest.mark.asyncio
    async def test_real_api_call(self, mock_config):
        """Тест реального вызова API (только если есть настоящий ключ)."""
        # Этот тест выполняется только если установлен реальный API ключ
        if mock_config.openrouter.openrouter_api_key.startswith("test-"):
            pytest.skip("Нет реального API ключа для теста")
        
        provider = OpenRouterProvider()
        messages = [ConversationMessage(role="user", content="Привет, это тест!")]
        
        try:
            response = await provider.generate_response(messages)
            
            assert response.content is not None
            assert len(response.content) > 0
            assert response.provider == "openrouter"
            assert response.tokens_used > 0
            
        except APIAuthenticationError:
            pytest.skip("Неправильный API ключ")
        except APIQuotaExceededError:
            pytest.skip("Недостаточно средств на счете")
        finally:
            await provider.close()