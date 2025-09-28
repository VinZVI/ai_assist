"""
@file: test_deepseek_provider.py
@description: Тесты для DeepSeek AI провайдера
@dependencies: pytest, pytest-asyncio, unittest.mock, httpx
@created: 2025-09-20
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.config import AppConfig
from app.services.ai_providers.base import (
    AIResponse,
    APIAuthenticationError,
    APIConnectionError,
    APIQuotaExceededError,
    APIRateLimitError,
    ConversationMessage,
)
from app.services.ai_providers.deepseek import DeepSeekProvider


@pytest.mark.ai_providers
@pytest.mark.integration
class TestDeepSeekProviderInitialization:
    """Тесты инициализации DeepSeek провайдера."""

    def test_provider_initialization(self, mock_config: AppConfig) -> None:
        """Тест инициализации провайдера."""
        provider = DeepSeekProvider()

        assert provider.name == "deepseek"
        assert provider.provider_name == "deepseek"
        assert hasattr(provider, "_client")

    def test_provider_configuration_check(self, mock_config: AppConfig) -> None:
        """Тест проверки конфигурации провайдера."""
        provider = DeepSeekProvider()

        assert provider.is_configured() is True

        # Тест с пустым API ключом
        with patch(
            "app.services.ai_providers.deepseek.get_config",
        ) as mock_get_config:
            # Мок конфига с пустым ключом
            mock_empty_config = MagicMock()
            mock_empty_config.deepseek.deepseek_api_key = ""
            mock_empty_config.deepseek.is_configured.return_value = False
            mock_get_config.return_value = mock_empty_config

            provider_unconfigured = DeepSeekProvider()
            assert provider_unconfigured.is_configured() is False

    def test_provider_availability_check(self, mock_config: AppConfig) -> None:
        """Тест проверки доступности провайдера."""
        provider = DeepSeekProvider()

        # По умолчанию провайдер считается доступным если настроен
        # Note: is_available() is async, но в простых тестах можно
        # проверить is_configured()
        assert provider.is_configured() is True


@pytest.mark.ai_providers
@pytest.mark.integration
class TestDeepSeekAPIRequests:
    """Тесты HTTP запросов к DeepSeek API."""

    @pytest.fixture
    def provider(self, mock_config: AppConfig) -> DeepSeekProvider:
        """Провайдер для тестов."""
        return DeepSeekProvider()

    @pytest.fixture
    def sample_messages(self) -> list[ConversationMessage]:
        """Пример сообщений для тестов."""
        return [
            ConversationMessage(role="system", content="Ты полезный AI помощник."),
            ConversationMessage(role="user", content="Привет! Как дела?"),
        ]

    @pytest.mark.asyncio
    async def test_successful_api_request(
        self, provider: DeepSeekProvider, sample_messages: list[ConversationMessage]
    ) -> None:
        """Тест успешного API запроса."""
        # Мокаем HTTP ответ в стиле DeepSeek API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-deepseek-test",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "deepseek-chat",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": (
                            "Квантовая физика изучает поведение частиц "
                            "на атомном уровне..."
                        ),
                    },
                    "finish_reason": "stop",
                },
            ],
            "usage": {
                "prompt_tokens": 35,
                "completion_tokens": 45,
                "total_tokens": 80,
            },
        }

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            response = await provider.generate_response(sample_messages)

            assert isinstance(response, AIResponse)
            assert "Квантовая физика" in response.content
            assert response.model == "deepseek-chat"
            assert response.provider == "deepseek"
            assert response.tokens_used == 80
            assert response.cached is False

    @pytest.mark.asyncio
    async def test_api_request_with_parameters(
        self, provider: DeepSeekProvider, sample_messages: list[ConversationMessage]
    ) -> None:
        """Тест API запроса с дополнительными параметрами."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Ответ с параметрами"}}],
            "usage": {"total_tokens": 30},
            "model": "deepseek-chat",
        }

        with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            await provider.generate_response(
                sample_messages,
                temperature=0.9,
                max_tokens=1500,
            )

            # Проверяем что параметры переданы в запрос
            call_kwargs = mock_post.call_args[1]
            request_data = call_kwargs["json"]

            assert request_data["temperature"] == 0.9
            assert request_data["max_tokens"] == 1500
            assert request_data["model"] == "deepseek-chat"

    @pytest.mark.asyncio
    async def test_http_headers(
        self, provider: DeepSeekProvider, sample_messages: list[ConversationMessage]
    ) -> None:
        """Тест правильных HTTP заголовков."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Тест заголовков"}}],
            "usage": {"total_tokens": 10},
            "model": "deepseek-chat",
        }

        with (
            patch("httpx.AsyncClient.post", return_value=mock_response),
            patch(
                "httpx.AsyncClient.__init__",
                return_value=None,
            ) as mock_client_init,
        ):
            # Принудительно очищаем клиент
            provider._client = None

            await provider.generate_response(sample_messages)

            # Проверяем заголовки при создании клиента
            mock_client_init.assert_called_once()
            call_kwargs = mock_client_init.call_args[1]
            headers = call_kwargs.get("headers", {})

            assert "Authorization" in headers
            assert headers["Authorization"].startswith("Bearer ")
            assert headers["Content-Type"] == "application/json"
            assert "User-Agent" in headers


@pytest.mark.ai_providers
@pytest.mark.integration
class TestDeepSeekErrorHandling:
    """Тесты обработки ошибок DeepSeek API."""

    @pytest.fixture
    def provider(self, mock_config: AppConfig) -> DeepSeekProvider:
        """Провайдер для тестов ошибок."""
        return DeepSeekProvider()

    @pytest.fixture
    def sample_messages(self) -> list[ConversationMessage]:
        """Сообщения для тестов ошибок."""
        return [ConversationMessage(role="user", content="Тест ошибок DeepSeek")]

    @pytest.mark.asyncio
    async def test_specific_deepseek_errors(
        self, provider: DeepSeekProvider, sample_messages: list[ConversationMessage]
    ) -> None:
        """Тест специфичных ошибок DeepSeek."""
        # Тест ошибки модели
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "message": "Model not found",
                "type": "invalid_request_error",
            },
        }

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            with pytest.raises(
                APIConnectionError,
                match="Ошибка запроса к DeepSeek API: Model not found",
            ):
                await provider.generate_response(sample_messages)

    @pytest.mark.asyncio
    async def test_server_error(
        self, provider: DeepSeekProvider, sample_messages: list[ConversationMessage]
    ) -> None:
        """Тест серверной ошибки (5xx)."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            with pytest.raises(
                APIConnectionError,
                match="Ошибка сервера DeepSeek: 500",
            ):
                await provider.generate_response(sample_messages)

    @pytest.mark.asyncio
    async def test_connection_timeout(
        self, provider: DeepSeekProvider, sample_messages: list[ConversationMessage]
    ) -> None:
        """Тест таймаута соединения."""
        with (
            patch(
                "httpx.AsyncClient.post",
                side_effect=httpx.TimeoutException("Request timed out"),
            ),
            pytest.raises(
                APIConnectionError,
                match="Timeout при обращении к DeepSeek API",
            ),
        ):
            await provider.generate_response(sample_messages)


@pytest.mark.ai_providers
@pytest.mark.integration
class TestDeepSeekResponseParsing:
    """Тесты парсинга ответов DeepSeek API."""

    @pytest.fixture
    def provider(self, mock_config: AppConfig) -> DeepSeekProvider:
        """Провайдер для тестов парсинга."""
        return DeepSeekProvider()

    @pytest.mark.asyncio
    async def test_complete_response_parsing(self, provider: DeepSeekProvider) -> None:
        """Тест парсинга полного ответа."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "cmpl-test",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "deepseek-chat",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Полный ответ от DeepSeek",
                    },
                    "finish_reason": "stop",
                },
            ],
            "usage": {
                "prompt_tokens": 15,
                "completion_tokens": 10,
                "total_tokens": 25,
            },
        }

        messages = [ConversationMessage(role="user", content="Тест")]

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            response = await provider.generate_response(messages)

            assert response.content == "Полный ответ от DeepSeek"
            assert response.model == "deepseek-chat"
            assert response.provider == "deepseek"
            assert response.tokens_used == 25
            assert response.cached is False

    @pytest.mark.asyncio
    async def test_streaming_response_handling(
        self, provider: DeepSeekProvider
    ) -> None:
        """Тест обработки streaming ответов (если поддерживается)."""
        # DeepSeek может поддерживать streaming, тестируем базовую обработку
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Streaming не поддерживается"}}],
        }

        messages = [ConversationMessage(role="user", content="Тест streaming")]

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            response = await provider.generate_response(messages)

            assert "не поддерживается" in response.content

    @pytest.mark.asyncio
    async def test_chinese_content_handling(self, provider: DeepSeekProvider) -> None:
        """Тест обработки китайского контента
        (DeepSeek специализируется на китайском)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "你好世界"}}
            ],  # "Hello World" in Chinese
            "usage": {"total_tokens": 10},
            "model": "deepseek-chat",
        }

        messages = [ConversationMessage(role="user", content="Привет на китайском")]

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            response = await provider.generate_response(messages)

            assert response.content == "你好世界"
            assert response.model == "deepseek-chat"


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
    #     assert all(
    #         msg["role"] in ["system", "user", "assistant"]
    #         for msg in formatted
    #     )
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
    async def test_provider_close(self, mock_config: AppConfig) -> None:
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
    def provider(self, mock_config: AppConfig) -> DeepSeekProvider:
        """Провайдер для тестов специфичных функций."""
        return DeepSeekProvider()

    @pytest.mark.asyncio
    async def test_code_generation_request(self, provider: DeepSeekProvider) -> None:
        """Тест запроса на генерацию кода (DeepSeek хорош в программировании)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": (
                            "``python\n"
                            "def fibonacci(n):\n"
                            "    if n <= 1:\n"
                            "        return n\n"
                            "    return fibonacci(n-1) + fibonacci(n-2)\n"
                            "```"
                        ),
                    },
                },
            ],
            "usage": {"total_tokens": 45},
            "model": "deepseek-coder",
        }

        messages = [
            ConversationMessage(
                role="user",
                content="Напиши функцию для вычисления чисел Фибоначчи на Python",
            ),
        ]

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            response = await provider.generate_response(messages)

            assert "fibonacci" in response.content.lower()
            assert "python" in response.content.lower()
            assert "```" in response.content

    @pytest.mark.asyncio
    async def test_math_problem_solving(self, provider: DeepSeekProvider) -> None:
        """Тест решения математических задач."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": (
                            "Для решения уравнения x² + 5x + 6 = 0:\n\n"
                            "Используем квадратную формулу:\n"
                            "x = (-5 ± √(25-24))/2 = (-5 ± 1)/2\n\n"
                            "Ответы: x₁ = -2, x₂ = -3"
                        ),
                    },
                },
            ],
            "usage": {"total_tokens": 65},
        }

        messages = [
            ConversationMessage(
                role="user",
                content="Реши уравнение x² + 5x + 6 = 0",
            ),
        ]

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            response = await provider.generate_response(messages)

            assert "x₁ = -2" in response.content
            assert "x₂ = -3" in response.content


@pytest.mark.ai_providers
@pytest.mark.slow
@pytest.mark.integration
class TestDeepSeekRealAPI:
    """Тесты с реальным DeepSeek API (медленные)."""

    @pytest.mark.asyncio
    async def test_real_api_connection(self, mock_config: AppConfig) -> None:
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
