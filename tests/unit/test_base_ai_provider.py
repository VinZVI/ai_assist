"""
@file: test_base_ai_provider.py
@description: Тесты для базового AI провайдера и связанных структур данных
@dependencies: pytest, pytest-asyncio, unittest.mock
@created: 2025-09-20
"""

from abc import ABC
from datetime import datetime
from typing import Any

import pytest

from app.services.ai_providers.base import (
    AIProviderError,
    AIResponse,
    APIAuthenticationError,
    APIConnectionError,
    APIQuotaExceededError,
    APIRateLimitError,
    BaseAIProvider,
    ConversationMessage,
)


@pytest.mark.ai_providers
@pytest.mark.unit
class TestConversationMessage:
    """Тесты для структуры ConversationMessage."""

    def test_message_creation(self) -> None:
        """Тест создания сообщения диалога."""
        msg = ConversationMessage(
            role="user",
            content="Привет, как дела?",
        )

        assert msg.role == "user"
        assert msg.content == "Привет, как дела?"
        assert msg.timestamp is None  # По умолчанию None

    def test_message_with_timestamp(self) -> None:
        """Тест создания сообщения с временной меткой."""
        now = datetime.now()
        msg = ConversationMessage(
            role="assistant",
            content="Привет! У меня всё отлично!",
            timestamp=now,
        )

        assert msg.role == "assistant"
        assert msg.content == "Привет! У меня всё отлично!"
        assert msg.timestamp == now

    def test_message_roles_validation(self) -> None:
        """Тест валидации ролей сообщений."""
        # Валидные роли
        valid_roles = ["system", "user", "assistant"]

        for role in valid_roles:
            msg = ConversationMessage(role=role, content="Тестовое сообщение")
            assert msg.role == role

    def test_message_equality(self) -> None:
        """Тест сравнения сообщений."""
        msg1 = ConversationMessage(role="user", content="Тест")
        msg2 = ConversationMessage(role="user", content="Тест")
        msg3 = ConversationMessage(role="user", content="Другой тест")

        assert msg1.role == msg2.role
        assert msg1.content == msg2.content
        assert msg1.content != msg3.content

    def test_message_string_representation(self) -> None:
        """Тест строкового представления сообщения."""
        msg = ConversationMessage(role="user", content="Короткий тест")

        # Должно содержать роль и контент
        str_repr = str(msg)
        assert "user" in str_repr
        assert "Короткий тест" in str_repr


@pytest.mark.ai_providers
@pytest.mark.unit
class TestAIResponse:
    """Тесты для структуры AIResponse."""

    def test_response_creation(self) -> None:
        """Тест создания AI ответа."""
        response = AIResponse(
            content="Это ответ от AI",
            model="test-model-v1",
            provider="test-provider",
            tokens_used=42,
            response_time=1.5,
        )

        assert response.content == "Это ответ от AI"
        assert response.model == "test-model-v1"
        assert response.provider == "test-provider"
        assert response.tokens_used == 42
        assert response.response_time == 1.5
        assert response.cached is False  # По умолчанию

    def test_cached_response(self) -> None:
        """Тест кешированного ответа."""
        response = AIResponse(
            content="Кешированный ответ",
            model="cache-model",
            provider="cache-provider",
            tokens_used=0,  # Кеш не тратит токены
            response_time=0.1,  # Быстрый ответ из кеша
            cached=True,
        )

        assert response.cached is True
        assert response.tokens_used == 0
        assert response.response_time == 0.1

    def test_response_with_minimal_data(self) -> None:
        """Тест ответа с минимальными данными."""
        response = AIResponse(
            content="Минимальный ответ",
            model="unknown",
            provider="unknown",
            tokens_used=0,
            response_time=0.0,
        )

        assert response.content == "Минимальный ответ"
        assert response.model == "unknown"
        assert response.provider == "unknown"

    def test_response_string_representation(self) -> None:
        """Тест строкового представления ответа."""
        response = AIResponse(
            content="Тестовый ответ для repr",
            model="repr-model",
            provider="repr-provider",
            tokens_used=25,
            response_time=0.8,
        )

        str_repr = str(response)
        assert "repr-provider" in str_repr
        assert "repr-model" in str_repr


@pytest.mark.ai_providers
@pytest.mark.unit
class TestAIProviderErrors:
    """Тесты для иерархии ошибок AI провайдеров."""

    def test_base_ai_provider_error(self) -> None:
        """Тест базовой ошибки AI провайдера."""
        error = AIProviderError("Базовая ошибка AI", "test-provider")

        assert str(error) == "Базовая ошибка AI"
        assert isinstance(error, Exception)

    def test_api_connection_error(self) -> None:
        """Тест ошибки подключения к API."""
        error = APIConnectionError("Не удалось подключиться к API", "test-provider")

        assert str(error) == "Не удалось подключиться к API"
        assert isinstance(error, AIProviderError)

    def test_api_authentication_error(self) -> None:
        """Тест ошибки аутентификации."""
        error = APIAuthenticationError("Неверный API ключ", "test-provider")

        assert str(error) == "Неверный API ключ"
        assert isinstance(error, AIProviderError)

    def test_api_rate_limit_error(self) -> None:
        """Тест ошибки превышения лимита."""
        error = APIRateLimitError("Превышен лимит запросов", "test-provider")

        assert str(error) == "Превышен лимит запросов"
        assert isinstance(error, AIProviderError)

    def test_api_quota_exceeded_error(self) -> None:
        """Тест ошибки превышения квоты."""
        error = APIQuotaExceededError("Превышена квота API", "test-provider")

        assert str(error) == "Превышена квота API"
        assert isinstance(error, AIProviderError)

    def test_error_hierarchy(self) -> None:
        """Тест иерархии ошибок."""
        # Все специфичные ошибки должны быть подклассами AIProviderError
        connection_error = APIConnectionError("Тест", "test-provider")
        auth_error = APIAuthenticationError("Тест", "test-provider")
        rate_limit_error = APIRateLimitError("Тест", "test-provider")
        quota_error = APIQuotaExceededError("Тест", "test-provider")

        assert isinstance(connection_error, AIProviderError)
        assert isinstance(auth_error, AIProviderError)
        assert isinstance(rate_limit_error, AIProviderError)
        assert isinstance(quota_error, AIProviderError)


@pytest.mark.ai_providers
@pytest.mark.unit
class TestBaseAIProvider:
    """Тесты для абстрактного базового AI провайдера."""

    def test_base_provider_is_abstracttract(self) -> None:
        """Тест что BaseAIProvider является абстрактным классом."""
        assert issubclass(BaseAIProvider, ABC)

        # Попытка создать экземпляр должна вызвать ошибку
        with pytest.raises(TypeError):
            BaseAIProvider("test")

    def test_concrete_provider_implementation(self) -> None:
        """Тест конкретной реализации провайдера."""

        class TestProvider(BaseAIProvider):
            def __init__(self) -> None:
                self.name = "test-provider"

            @property
            def provider_name(self) -> str:
                return "test-provider"

            async def generate_response(
                self,
                messages: list[ConversationMessage],
                temperature: float | None = None,
                max_tokens: int | None = None,
                **kwargs: Any,
            ) -> AIResponse:
                return AIResponse(
                    content="Тестовый ответ",
                    model="test-model",
                    provider=self.name,
                    tokens_used=10,
                    response_time=0.5,
                )

            def is_configured(self) -> bool:
                return True

            async def is_available(self) -> bool:
                return True

            async def health_check(self) -> dict[str, str]:
                return {"status": "healthy"}

            async def close(self) -> None:
                pass

        # Должен создаваться без ошибок
        provider = TestProvider()
        assert provider.name == "test-provider"

    @pytest.mark.asyncio
    async def test_provider_interface_methods(self) -> None:
        """Тест интерфейса методов провайдера."""

        class MockProvider(BaseAIProvider):
            def __init__(self) -> None:
                self.name = "mock-provider"
                self._configured = True
                self._available = True

            @property
            def provider_name(self) -> str:
                return "mock-provider"

            async def generate_response(
                self,
                messages: list[ConversationMessage],
                temperature: float | None = None,
                max_tokens: int | None = None,
                **kwargs: Any,
            ) -> AIResponse:
                return AIResponse(
                    content=f"Ответ на {len(messages)} сообщений",
                    model="mock-model",
                    provider=self.name,
                    tokens_used=len(messages) * 5,
                    response_time=0.2,
                )

            def is_configured(self) -> bool:
                return self._configured

            async def is_available(self) -> bool:
                return self._available

            async def health_check(self) -> dict[str, str]:
                return {"status": "healthy" if self._available else "unhealthy"}

            async def close(self) -> None:
                self._available = False

        provider = MockProvider()

        # Тест is_configured
        assert provider.is_configured() is True

        # Тест is_available
        assert await provider.is_available() is True

        # Тест generate_response
        messages = [
            ConversationMessage(role="user", content="Тест 1"),
            ConversationMessage(role="user", content="Тест 2"),
        ]

        response = await provider.generate_response(messages)
        assert response.content == "Ответ на 2 сообщений"
        assert response.tokens_used == 10
        assert response.provider == "mock-provider"

        # Тест close
        await provider.close()
        assert await provider.is_available() is False

    @pytest.mark.asyncio
    async def test_provider_configuration_states(self) -> None:
        """Тест различных состояний конфигурации провайдера."""

        class ConfigurableProvider(BaseAIProvider):
            def __init__(self, api_key: str | None = None) -> None:
                self.name = "configurable-provider"
                self._api_key = api_key

            @property
            def provider_name(self) -> str:
                return "configurable-provider"

            async def generate_response(
                self,
                messages: list[ConversationMessage],
                temperature: float | None = None,
                max_tokens: int | None = None,
                **kwargs: Any,
            ) -> AIResponse:
                if not self.is_configured():
                    msg = "Провайдер не настроен"
                    raise APIAuthenticationError(
                        msg,
                        "configurable",
                    )
                return AIResponse(
                    content="Настроенный ответ",
                    model="config-model",
                    provider=self.name,
                    tokens_used=5,
                    response_time=0.3,
                )

            def is_configured(self) -> bool:
                return self._api_key is not None and self._api_key != ""

            async def is_available(self) -> bool:
                return self.is_configured()

            async def health_check(self) -> dict[str, str]:
                return {"status": "healthy" if self.is_configured() else "unhealthy"}

            async def close(self) -> None:
                pass

        # Провайдер без конфигурации
        unconfigured_provider = ConfigurableProvider()
        assert unconfigured_provider.is_configured() is False
        assert await unconfigured_provider.is_available() is False

        # Провайдер с пустым ключом
        empty_key_provider = ConfigurableProvider("")
        assert empty_key_provider.is_configured() is False

        # Настроенный провайдер
        configured_provider = ConfigurableProvider("valid-api-key")
        assert configured_provider.is_configured() is True
        assert await configured_provider.is_available() is True

    @pytest.mark.asyncio
    async def test_provider_error_handling(self) -> None:
        """Тест обработки ошибок в провайдере."""

        class ErrorProvider(BaseAIProvider):
            def __init__(self, error_type: str | None = None) -> None:
                self.name = "error-provider"
                self._error_type = error_type

            @property
            def provider_name(self) -> str:
                return "error-provider"

            async def generate_response(
                self,
                messages: list[ConversationMessage],
                temperature: float | None = None,
                max_tokens: int | None = None,
                **kwargs: Any,
            ) -> AIResponse:
                # Используем аргументы чтобы избежать предупреждений
                _ = messages, temperature, max_tokens, kwargs
                if self._error_type == "auth":
                    msg = "Ошибка аутентификации"
                    raise APIAuthenticationError(msg, "error")
                if self._error_type == "rate_limit":
                    msg = "Превышен лимит"
                    raise APIRateLimitError(msg, "error")
                if self._error_type == "connection":
                    msg = "Ошибка соединения"
                    raise APIConnectionError(msg, "error")
                if self._error_type == "quota":
                    msg = "Превышена квота"
                    raise APIQuotaExceededError(msg, "error-provider")

                return AIResponse(
                    content="Успешный ответ",
                    model="error-model",
                    provider=self.name,
                    tokens_used=1,
                    response_time=0.1,
                )

            def is_configured(self) -> bool:
                return True

            async def is_available(self) -> bool:
                return True

            async def health_check(self) -> dict[str, str]:
                return {"status": "healthy"}

            async def close(self) -> None:
                pass

        messages = [ConversationMessage(role="user", content="Тест ошибок")]

        # Тест различных типов ошибок
        auth_provider = ErrorProvider("auth")
        with pytest.raises(APIAuthenticationError):
            await auth_provider.generate_response(messages)

        rate_provider = ErrorProvider("rate_limit")
        with pytest.raises(APIRateLimitError):
            await rate_provider.generate_response(messages)

        connection_provider = ErrorProvider("connection")
        with pytest.raises(APIConnectionError):
            await connection_provider.generate_response(messages)

        quota_provider = ErrorProvider("quota")
        with pytest.raises(APIQuotaExceededError):
            await quota_provider.generate_response(messages)

        # Тест успешного выполнения
        success_provider = ErrorProvider()
        response = await success_provider.generate_response(messages)
        assert response.content == "Успешный ответ"


@pytest.mark.ai_providers
@pytest.mark.unit
class TestProviderParameterHandling:
    """Тесты обработки параметров в провайдерах."""

    @pytest.mark.asyncio
    async def test_parameter_passing(self) -> None:
        """Тест передачи параметров в провайдер."""

        class ParameterProvider(BaseAIProvider):
            def __init__(self) -> None:
                self.name = "parameter-provider"
                self.last_params = {}

            @property
            def provider_name(self) -> str:
                return "parameter-provider"

            async def generate_response(
                self,
                messages: list[ConversationMessage],
                temperature: float | None = None,
                max_tokens: int | None = None,
                **kwargs: Any,
            ) -> AIResponse:
                # Используем аргументы чтобы избежать предупреждений
                _ = messages
                self.last_params = {
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "kwargs": kwargs,
                }

                return AIResponse(
                    content=f"Temp: {temperature}, Tokens: {max_tokens}",
                    model="param-model",
                    provider=self.name,
                    tokens_used=1,
                    response_time=0.1,
                )

            def is_configured(self) -> bool:
                return True

            async def is_available(self) -> bool:
                return True

            async def health_check(self) -> dict[str, str]:
                return {"status": "healthy"}

            async def close(self) -> None:
                pass

        provider = ParameterProvider()
        messages = [ConversationMessage(role="user", content="Тест параметров")]

        # Тест с параметрами
        await provider.generate_response(
            messages,
            temperature=0.8,
            max_tokens=1000,
            custom_param="test_value",
        )

        assert provider.last_params["temperature"] == 0.8
        assert provider.last_params["max_tokens"] == 1000
        assert provider.last_params["kwargs"]["custom_param"] == "test_value"

        # Тест без параметров
        await provider.generate_response(messages)

        assert provider.last_params["temperature"] is None
        assert provider.last_params["max_tokens"] is None
        assert provider.last_params["kwargs"] == {}


@pytest.mark.ai_providers
@pytest.mark.unit
class TestProviderLifecycle:
    """Тесты жизненного цикла AI провайдеров."""

    @pytest.mark.asyncio
    async def test_provider_context_manager(self) -> None:
        """Тест использования провайдера как async context manager."""

        class ContextProvider(BaseAIProvider):
            def __init__(self) -> None:
                self.name = "context-provider"
                self.closed = False

            @property
            def provider_name(self) -> str:
                return "context-provider"

            async def generate_response(
                self,
                messages: list[ConversationMessage],
                temperature: float | None = None,
                max_tokens: int | None = None,
                **kwargs: Any,
            ) -> AIResponse:
                # Используем аргументы чтобы избежать предупреждений
                _ = messages, temperature, max_tokens, kwargs
                if self.closed:
                    msg = "Провайдер закрыт"
                    raise APIConnectionError(msg, "context")

                return AIResponse(
                    content="Ответ от контекстного провайдера",
                    model="context-model",
                    provider=self.name,
                    tokens_used=5,
                    response_time=0.2,
                )

            def is_configured(self) -> bool:
                return True

            async def is_available(self) -> bool:
                return not self.closed

            async def health_check(self) -> dict[str, str]:
                return {"status": "healthy"}

            async def close(self) -> None:
                self.closed = True

            async def __aenter__(self) -> "ContextProvider":
                return self

            async def __aexit__(
                self,
                exc_type: type[BaseException] | None,
                exc_val: BaseException | None,
                exc_tb: object | None,
            ) -> None:
                await self.close()

        # Тест использования как context manager
        async with ContextProvider() as provider:
            assert await provider.is_available() is True

            messages = [ConversationMessage(role="user", content="Контекст тест")]
            response = await provider.generate_response(messages)
            assert response.content == "Ответ от контекстного провайдера"

        # После выхода из контекста провайдер должен быть закрыт
        assert provider.closed is True
        assert await provider.is_available() is False
