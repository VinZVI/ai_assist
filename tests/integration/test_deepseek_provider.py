"""
@file: test_deepseek_provider.py
@description: Тесты для DeepSeek AI провайдера
@dependencies: pytest, pytest-asyncio, unittest.mock, httpx
@created: 2025-09-20
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.ai_providers.deepseek import DeepSeekProvider
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
class TestDeepSeekProviderInitialization:
    """Тесты инициализации DeepSeek провайдера."""
    
    def test_provider_initialization(self, mock_config):
        """Тест инициализации провайдера."""
        provider = DeepSeekProvider()
        
        assert provider.name == "deepseek"
        assert provider.provider_name == "deepseek"
        assert hasattr(provider, '_client')
    
    def test_provider_configuration_check(self, mock_config):
        """Тест проверки конфигурации провайдера."""
        provider = DeepSeekProvider()
        
        assert provider.is_configured() is True
        
        # Тест с пустым API ключом
        with patch('app.services.ai_providers.deepseek.get_config') as mock_get_config:
            # Мок конфига с пустым ключом
            mock_empty_config = MagicMock()
            mock_empty_config.deepseek.deepseek_api_key = ""
            mock_empty_config.deepseek.is_configured.return_value = False
            mock_get_config.return_value = mock_empty_config
            
            provider_unconfigured = DeepSeekProvider()
            assert provider_unconfigured.is_configured() is False
    
    def test_provider_availability_check(self, mock_config):
        """Тест проверки доступности провайдера."""
        provider = DeepSeekProvider()
        
        # По умолчанию провайдер считается доступным если настроен
        # Note: is_available() is async, но в простых тестах можно проверить is_configured()
        assert provider.is_configured() is True


@pytest.mark.ai_providers
@pytest.mark.integration
class TestDeepSeekAPIRequests:
    """Тесты HTTP запросов к DeepSeek API."""
    
    @pytest.fixture
    def provider(self, mock_config):
        """Провайдер для тестов."""
        return DeepSeekProvider()
    
    @pytest.fixture
    def sample_messages(self):
        """Пример сообщений для тестов."""
        return [
            ConversationMessage(role="system", content="Ты полезный AI помощник."),
            ConversationMessage(role="user", content="Объясни квантовую физику простыми словами.")
        ]
    
    @pytest.mark.asyncio
    async def test_successful_api_request(self, provider, sample_messages):
        """Тест успешного API запроса."""
        # Мокаем HTTP ответ в стиле DeepSeek API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-deepseek-test",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "deepseek-chat",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Квантовая физика изучает поведение частиц на атомном уровне..."
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 35,
                "completion_tokens": 45,
                "total_tokens": 80
            }
        }
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            response = await provider.generate_response(sample_messages)
            
            assert isinstance(response, AIResponse)
            assert "Квантовая физика" in response.content
            assert response.model == "deepseek-chat"
            assert response.provider == "deepseek"
            assert response.tokens_used == 80
            assert response.cached is False
    
    @pytest.mark.asyncio
    async def test_api_request_with_parameters(self, provider, sample_messages):
        """Тест API запроса с дополнительными параметрами."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Ответ с параметрами"}}],
            "usage": {"total_tokens": 30},
            "model": "deepseek-chat"
        }
        
        with patch('httpx.AsyncClient.post', return_value=mock_response) as mock_post:
            await provider.generate_response(
                sample_messages,
                temperature=0.9,
                max_tokens=1500
            )
            
            # Проверяем что параметры переданы в запрос
            call_kwargs = mock_post.call_args[1]
            request_data = call_kwargs['json']
            
            assert request_data['temperature'] == 0.9
            assert request_data['max_tokens'] == 1500
            assert request_data['model'] == "deepseek-chat"
    
    @pytest.mark.asyncio
    async def test_http_headers(self, provider, sample_messages):
        """Тест правильных HTTP заголовков."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Тест заголовков"}}],
            "usage": {"total_tokens": 10},
            "model": "deepseek-chat"
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
                assert "User-Agent" in headers


@pytest.mark.ai_providers
@pytest.mark.integration
class TestDeepSeekErrorHandling:
    """Тесты обработки ошибок DeepSeek API."""
    
    @pytest.fixture
    def provider(self, mock_config):
        """Провайдер для тестов ошибок."""
        return DeepSeekProvider()
    
    @pytest.fixture  
    def sample_messages(self):
        """Сообщения для тестов ошибок."""
        return [ConversationMessage(role="user", content="Тест ошибок DeepSeek")]
    
    @pytest.mark.asyncio
    async def test_authentication_error(self, provider, sample_messages):
        """Тест ошибки аутентификации (401)."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid API key",
                "type": "invalid_request_error",
                "code": "invalid_api_key"
            }
        }
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            with pytest.raises(APIAuthenticationError, match="Неверный API ключ DeepSeek"):
                await provider.generate_response(sample_messages)
    
    @pytest.mark.asyncio
    async def test_quota_exceeded_error(self, provider, sample_messages):
        """Тест ошибки превышения квоты (402)."""
        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_response.json.return_value = {
            "error": {
                "message": "Insufficient quota",
                "type": "insufficient_quota",
                "code": "insufficient_quota"
            }
        }
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            with pytest.raises(APIQuotaExceededError, match="Недостаточно средств на счете DeepSeek API"):
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
            with pytest.raises(APIRateLimitError, match="Превышен лимит запросов к DeepSeek API"):
                await provider.generate_response(sample_messages)
    
    @pytest.mark.asyncio
    async def test_specific_deepseek_errors(self, provider, sample_messages):
        """Тест специфичных ошибок DeepSeek."""
        # Тест ошибки модели
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "message": "Model not found",
                "type": "invalid_request_error"
            }
        }
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            with pytest.raises(APIConnectionError, match="Model not found"):
                await provider.generate_response(sample_messages)
    
    @pytest.mark.asyncio
    async def test_server_error(self, provider, sample_messages):
        """Тест серверной ошибки (5xx)."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service Temporarily Unavailable"
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            with pytest.raises(APIConnectionError, match="Ошибка сервера DeepSeek: 503"):
                await provider.generate_response(sample_messages)
    
    @pytest.mark.asyncio
    async def test_connection_timeout(self, provider, sample_messages):
        """Тест таймаута соединения."""
        with patch('httpx.AsyncClient.post', side_effect=httpx.TimeoutException("Request timeout")):
            with pytest.raises(APIConnectionError, match="Timeout при обращении к DeepSeek API"):
                await provider.generate_response(sample_messages)


@pytest.mark.ai_providers
@pytest.mark.integration
class TestDeepSeekResponseParsing:
    """Тесты парсинга ответов DeepSeek API."""
    
    @pytest.fixture
    def provider(self, mock_config):
        """Провайдер для тестов парсинга."""
        return DeepSeekProvider()
    
    @pytest.mark.asyncio
    async def test_complete_response_parsing(self, provider):
        """Тест парсинга полного ответа."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "deepseek-chat",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Полный ответ от DeepSeek с метаданными"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 25,
                "completion_tokens": 35,
                "total_tokens": 60
            }
        }
        
        messages = [ConversationMessage(role="user", content="Тест парсинга")]
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            response = await provider.generate_response(messages)
            
            assert response.content == "Полный ответ от DeepSeek с метаданными"
            assert response.tokens_used == 60
            assert response.model == "deepseek-chat"
            assert response.provider == "deepseek"
    
    @pytest.mark.asyncio
    async def test_streaming_response_handling(self, provider):
        """Тест обработки streaming ответов (если поддерживается)."""
        # DeepSeek может поддерживать streaming, тестируем базовую обработку
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Streaming ответ"}}],
            "usage": {"total_tokens": 15}
        }
        
        messages = [ConversationMessage(role="user", content="Streaming тест")]
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            response = await provider.generate_response(messages)
            
            assert "Streaming ответ" in response.content
    
    @pytest.mark.asyncio
    async def test_chinese_content_handling(self, provider):
        """Тест обработки китайского контента (DeepSeek специализируется на китайском)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "你好！我是DeepSeek AI助手。"}}],
            "usage": {"total_tokens": 20},
            "model": "deepseek-chat"
        }
        
        messages = [ConversationMessage(role="user", content="你好")]
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            response = await provider.generate_response(messages)
            
            assert "你好！我是DeepSeek AI助手。" in response.content
            assert response.tokens_used == 20


@pytest.mark.ai_providers
@pytest.mark.unit
class TestDeepSeekHelperMethods:
    """Тесты вспомогательных методов DeepSeek провайдера."""
    
    # def test_message_formatting(self, mock_config):
    #     """Тест форматирования сообщений для DeepSeek API."""
    #     provider = DeepSeekProvider()
    #     
    #     messages = [
    #         ConversationMessage(role="system", content="Ты эксперт по AI"),
    #         ConversationMessage(role="user", content="Расскажи о нейросетях"),
    #         ConversationMessage(role="assistant", content="Нейросети это...")
    #     ]
    #     
    #     formatted = provider._format_messages(messages)
    #     
    #     assert len(formatted) == 3
    #     assert all(msg["role"] in ["system", "user", "assistant"] for msg in formatted)
    #     assert formatted[0]["content"] == "Ты эксперт по AI"
    
    # def test_request_preparation(self, mock_config):
    #     """Тест подготовки запроса."""
    #     provider = DeepSeekProvider()
    #     
    #     messages = [ConversationMessage(role="user", content="Тест запроса")]
    #     
    #     request_data = provider._prepare_request_data(
    #         messages,
    #         temperature=0.7,
    #         max_tokens=2000
    #     )
    #     
    #     assert request_data["model"] == mock_config.deepseek.deepseek_model
    #     assert request_data["temperature"] == 0.7
    #     assert request_data["max_tokens"] == 2000
    #     assert "messages" in request_data
    
    # def test_error_extraction(self, mock_config):
    #     """Тест извлечения ошибок из ответа."""
    #     provider = DeepSeekProvider()
    #     
    #     error_response = {
    #         "error": {
    #             "message": "Test error message",
    #             "type": "test_error",
    #             "code": "test_code"
    #         }
    #     }
    #     
    #     error_msg = provider._extract_error_message(error_response)
    #     assert "Test error message" in error_msg


@pytest.mark.ai_providers
@pytest.mark.integration
class TestDeepSeekProviderLifecycle:
    """Тесты жизненного цикла DeepSeek провайдера."""
    
    @pytest.mark.asyncio
    async def test_provider_close(self, mock_config):
        """Тест закрытия провайдера."""
        provider = DeepSeekProvider()
        
        # Создаем мок клиента
        mock_client = AsyncMock()
        provider._client = mock_client
        
        await provider.close()
        
        mock_client.aclose.assert_called_once()
        assert provider._client is None
    
    # @pytest.mark.asyncio
    # async def test_context_manager_usage(self, mock_config):
    #     """Тест использования провайдера как context manager."""
    #     async with DeepSeekProvider(mock_config.deepseek) as provider:
    #         assert provider is not None
    #         assert hasattr(provider, '_config')
    #     
    #     # После выхода из контекста провайдер должен быть закрыт
    #     assert provider._client is None


@pytest.mark.ai_providers
@pytest.mark.integration
class TestDeepSeekSpecificFeatures:
    """Тесты специфичных особенностей DeepSeek."""
    
    @pytest.fixture
    def provider(self, mock_config):
        """Провайдер для тестов специфичных функций."""
        return DeepSeekProvider()
    
    @pytest.mark.asyncio
    async def test_code_generation_request(self, provider):
        """Тест запроса на генерацию кода (DeepSeek хорош в программировании)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n```"
                }
            }],
            "usage": {"total_tokens": 45},
            "model": "deepseek-coder"
        }
        
        messages = [ConversationMessage(
            role="user", 
            content="Напиши функцию для вычисления чисел Фибоначчи на Python"
        )]
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            response = await provider.generate_response(messages)
            
            assert "fibonacci" in response.content.lower()
            assert "python" in response.content.lower()
            assert "```" in response.content
    
    @pytest.mark.asyncio
    async def test_math_problem_solving(self, provider):
        """Тест решения математических задач."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Для решения уравнения x² + 5x + 6 = 0:\n\nИспользуем квадратную формулу:\nx = (-5 ± √(25-24))/2 = (-5 ± 1)/2\n\nОтветы: x₁ = -2, x₂ = -3"
                }
            }],
            "usage": {"total_tokens": 65}
        }
        
        messages = [ConversationMessage(
            role="user",
            content="Реши уравнение x² + 5x + 6 = 0"
        )]
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            response = await provider.generate_response(messages)
            
            assert "x₁ = -2" in response.content
            assert "x₂ = -3" in response.content


@pytest.mark.ai_providers
@pytest.mark.slow
@pytest.mark.integration  
class TestDeepSeekRealAPI:
    """Тесты с реальным DeepSeek API (медленные)."""
    
    @pytest.mark.asyncio
    async def test_real_api_connection(self, mock_config):
        """Тест реального подключения к DeepSeek API."""
        # Этот тест выполняется только если есть настоящий ключ
        if mock_config.deepseek.deepseek_api_key.startswith("test-"):
            pytest.skip("Нет реального API ключа для теста")
        
        provider = DeepSeekProvider()
        messages = [ConversationMessage(role="user", content="Привет, DeepSeek!")]
        
        try:
            response = await provider.generate_response(messages)
            
            assert response.content is not None
            assert len(response.content) > 0
            assert response.provider == "deepseek"
            assert response.tokens_used > 0
            
        except APIAuthenticationError:
            pytest.skip("Неправильный API ключ DeepSeek")
        except APIQuotaExceededError:
            pytest.skip("Недостаточно средств на счете DeepSeek")
        finally:
            await provider.close()