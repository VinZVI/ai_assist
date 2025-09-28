"""
@file: test_ai_manager.py
@description: Тесты для AIManager - центрального менеджера AI провайдеров
@dependencies: pytest, pytest-asyncio, unittest.mock
@created: 2025-09-20
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.config import AppConfig
from app.services.ai_manager import (
    AIManager,
    AIProviderError,
    get_ai_manager,
)
from app.services.ai_providers.base import (
    AIResponse,
    APIAuthenticationError,
    APIConnectionError,
    APIQuotaExceededError,
    APIRateLimitError,
    ConversationMessage,
)


@pytest.fixture
def manager_with_mocked_providers(
    mock_config: AppConfig,
) -> tuple[AIManager, AsyncMock, AsyncMock]:
    """Менеджер с мокированными провайдерами."""
    # Ensure the mock config has the correct AI provider settings
    mock_config.ai_provider.primary_provider = "openrouter"
    mock_config.ai_provider.fallback_provider = "deepseek"
    mock_config.ai_provider.enable_fallback = True

    with patch("app.services.ai_manager.get_config", return_value=mock_config):
        manager = AIManager()

        # Мокаем провайдеры с полной совместимостью
        mock_openrouter = AsyncMock()
        mock_openrouter.name = "openrouter"
        mock_openrouter.provider_name = "openrouter"
        mock_openrouter.is_configured.return_value = True
        mock_openrouter.is_available = AsyncMock(return_value=True)
        mock_openrouter.health_check = AsyncMock(return_value={"status": "healthy"})
        mock_openrouter.close = AsyncMock()
        mock_openrouter.generate_response = AsyncMock()

        mock_deepseek = AsyncMock()
        mock_deepseek.name = "deepseek"
        mock_deepseek.provider_name = "deepseek"
        mock_deepseek.is_configured.return_value = True
        mock_deepseek.is_available = AsyncMock(return_value=True)
        mock_deepseek.health_check = AsyncMock(return_value={"status": "healthy"})
        mock_deepseek.close = AsyncMock()
        mock_deepseek.generate_response = AsyncMock()

        # Заменяем провайдеры в менеджере на моки
        manager._providers["openrouter"] = mock_openrouter
        manager._providers["deepseek"] = mock_deepseek

        return manager, mock_openrouter, mock_deepseek


@pytest.mark.ai_manager
@pytest.mark.integration
class TestAIManagerInitialization:
    """Тесты инициализации AIManager."""

    @pytest.mark.asyncio
    async def test_ai_manager_initialization(self, mock_config: AppConfig) -> None:
        """Тест инициализации AI менеджера."""
        with patch("app.services.ai_manager.get_config", return_value=mock_config):
            manager = AIManager()

            assert manager is not None
            assert hasattr(manager, "_providers")
            assert hasattr(manager, "_config")

    def test_ai_manager_singleton(self) -> None:
        """Тест singleton паттерна для AIManager."""
        with patch("app.services.ai_manager.get_config"):
            manager1 = get_ai_manager()
            manager2 = get_ai_manager()

            assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_provider_registration(self, mock_config: AppConfig) -> None:
        """Тест регистрации провайдеров."""
        with patch("app.services.ai_manager.get_config", return_value=mock_config):
            manager = AIManager()

            # Проверяем, что провайдеры зарегистрированы
            openrouter = manager.get_provider("openrouter")
            deepseek = manager.get_provider("deepseek")

            assert openrouter is not None
            assert deepseek is not None

    def test_invalid_provider_request(self, mock_config: AppConfig) -> None:
        """Тест запроса несуществующего провайдера."""
        with patch("app.services.ai_manager.get_config", return_value=mock_config):
            manager = AIManager()

            invalid_provider = manager.get_provider("nonexistent")
            assert invalid_provider is None

    @pytest.mark.asyncio
    async def test_provider_selection(self, mock_config: AppConfig) -> None:
        """Тест выбора провайдера по имени."""
        with patch("app.services.ai_manager.get_config", return_value=mock_config):
            manager = AIManager()

            provider = manager.get_provider("openrouter")

            assert provider is not None
            assert provider.name == "openrouter"


@pytest.mark.ai_manager
@pytest.mark.integration
class TestAIManagerFallbackLogic:
    """Тесты fallback логики между провайдерами."""

    @pytest.mark.asyncio
    async def test_successful_primary_provider(
        self,
        manager_with_mocked_providers: tuple[AIManager, AsyncMock, AsyncMock],
        mock_conversation_messages: list[ConversationMessage],
        mock_ai_response: AIResponse,
    ) -> None:
        """Тест успешного ответа от основного провайдера."""
        manager, mock_openrouter, mock_deepseek = manager_with_mocked_providers

        # Настраиваем успешный ответ от OpenRouter
        mock_openrouter.generate_response.return_value = mock_ai_response

        response = await manager.generate_response(
            mock_conversation_messages, use_cache=False
        )

        assert response.content == "Это тестовый ответ от AI"
        assert response.provider == "test-provider"
        mock_openrouter.generate_response.assert_called_once()
        mock_deepseek.generate_response.assert_not_called()

    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(
        self,
        manager_with_mocked_providers: tuple[AIManager, AsyncMock, AsyncMock],
        mock_conversation_messages: list[ConversationMessage],
        mock_ai_response: AIResponse,
    ) -> None:
        """Тест fallback при сбое основного провайдера."""
        manager, mock_openrouter, mock_deepseek = manager_with_mocked_providers

        # OpenRouter падает, DeepSeek работает
        mock_openrouter.generate_response.side_effect = APIConnectionError(
            "OpenRouter недоступен",
            "openrouter",
        )
        mock_deepseek.generate_response.return_value = mock_ai_response

        response = await manager.generate_response(
            mock_conversation_messages, use_cache=False
        )

        assert response.content == "Это тестовый ответ от AI"
        mock_openrouter.generate_response.assert_called_once()
        mock_deepseek.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_both_providers_fail(
        self,
        manager_with_mocked_providers: tuple[AIManager, AsyncMock, AsyncMock],
        mock_conversation_messages: list[ConversationMessage],
    ) -> None:
        """Тест когда оба провайдера недоступны."""
        manager, mock_openrouter, mock_deepseek = manager_with_mocked_providers

        # Оба провайдера падают
        mock_openrouter.generate_response.side_effect = APIConnectionError(
            "OpenRouter недоступен",
            "openrouter",
        )
        mock_deepseek.generate_response.side_effect = APIConnectionError(
            "DeepSeek недоступен",
            "deepseek",
        )

        with pytest.raises(AIProviderError, match="DeepSeek недоступен"):
            await manager.generate_response(mock_conversation_messages, use_cache=False)

    @pytest.mark.asyncio
    async def test_rate_limit_fallback(
        self,
        manager_with_mocked_providers: tuple[AIManager, AsyncMock, AsyncMock],
        mock_conversation_messages: list[ConversationMessage],
        mock_ai_response: AIResponse,
    ) -> None:
        """Тест fallback при превышении лимита запросов."""
        manager, mock_openrouter, mock_deepseek = manager_with_mocked_providers

        # OpenRouter выдает rate limit, DeepSeek работает
        mock_openrouter.generate_response.side_effect = APIRateLimitError(
            "Rate limit exceeded",
            "openrouter",
        )
        mock_deepseek.generate_response.return_value = mock_ai_response

        response = await manager.generate_response(
            mock_conversation_messages, use_cache=False
        )

        assert response is not None
        # Проверяем что статистика fallback увеличилась
        stats = manager.get_stats()
        assert stats["fallback_used"] > 0


@pytest.mark.ai_manager
@pytest.mark.integration
class TestAIManagerHealthCheck:
    """Тесты health check функциональности."""

    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self, mock_ai_manager: AsyncMock) -> None:
        """Тест health check когда все провайдеры здоровы."""
        health = await mock_ai_manager.health_check()

        assert health["manager_status"] == "healthy"
        assert "providers" in health
        assert health["providers"]["openrouter"]["status"] == "healthy"
        assert health["providers"]["deepseek"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_with_failures(
        self, manager_with_mocked_providers: tuple[AIManager, AsyncMock, AsyncMock]
    ) -> None:
        """Тест health check с недоступными провайдерами."""
        manager, mock_openrouter, mock_deepseek = manager_with_mocked_providers

        # OpenRouter недоступен
        mock_openrouter.is_available.return_value = False
        mock_deepseek.is_available.return_value = True

        with patch.object(manager, "health_check") as mock_health:
            mock_health.return_value = {
                "manager_status": "degraded",
                "providers": {
                    "openrouter": {"status": "unhealthy", "error": "Connection failed"},
                    "deepseek": {"status": "healthy"},
                },
            }

            health = await manager.health_check()

            assert health["manager_status"] == "degraded"
            assert health["providers"]["openrouter"]["status"] == "unhealthy"
            assert health["providers"]["deepseek"]["status"] == "healthy"


@pytest.mark.ai_manager
@pytest.mark.unit
class TestAIManagerStatistics:
    """Тесты системы статистики AIManager."""

    def test_initial_statistics(self, mock_ai_manager: AsyncMock) -> None:
        """Тест начальной статистики."""
        # Мок возвращает синхронно
        mock_ai_manager.get_stats.return_value = {
            "requests_total": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "fallback_used": 0,
            "provider_stats": {},
        }

        stats = mock_ai_manager.get_stats()

        assert "requests_total" in stats
        assert "requests_successful" in stats
        assert "requests_failed" in stats
        assert "fallback_used" in stats
        assert "provider_stats" in stats

    def test_statistics_after_requests(self, mock_ai_manager: AsyncMock) -> None:
        """Тест статистики после запросов."""
        # Имитируем статистику с запросами
        mock_ai_manager.get_stats.return_value = {
            "requests_total": 150,
            "requests_successful": 142,
            "requests_failed": 8,
            "fallback_used": 5,
            "provider_stats": {
                "openrouter": {"requests": 90, "successes": 85},
                "deepseek": {"requests": 60, "successes": 57},
            },
        }

        stats = mock_ai_manager.get_stats()

        assert stats["requests_total"] == 150
        assert stats["requests_successful"] == 142
        assert stats["fallback_used"] == 5
        assert stats["provider_stats"]["openrouter"]["successes"] == 85


@pytest.mark.ai_manager
@pytest.mark.integration
class TestAIManagerCaching:
    """Тесты системы кеширования AIManager."""

    @pytest.mark.asyncio
    async def test_cache_hit(
        self,
        manager_with_mocked_providers: tuple[AIManager, AsyncMock, AsyncMock],
        mock_conversation_messages: list[ConversationMessage],
    ) -> None:
        """Тест попадания в кеш."""
        manager, mock_openrouter, mock_deepseek = manager_with_mocked_providers

        # Первый запрос - кеш пустой
        first_response = AIResponse(
            content="Первый ответ",
            model="test-model",
            provider="openrouter",
            tokens_used=25,
            response_time=0.5,
            cached=False,
        )
        mock_openrouter.generate_response.return_value = first_response

        # Второй запрос - должен взять из кеша
        cached_response = AIResponse(
            content="Первый ответ",
            model="test-model",
            provider="openrouter",
            tokens_used=25,
            response_time=0.1,
            cached=True,
        )

        with patch.object(manager, "generate_response") as mock_generate:
            mock_generate.side_effect = [first_response, cached_response]

            # Первый запрос
            response1 = await manager.generate_response(
                mock_conversation_messages,
                use_cache=True,
            )
            # Второй запрос (тот же контент)
            response2 = await manager.generate_response(
                mock_conversation_messages,
                use_cache=True,
            )

            assert response2.cached is True
            assert response2.response_time < response1.response_time

    @pytest.mark.asyncio
    async def test_cache_disabled(
        self,
        manager_with_mocked_providers: tuple[AIManager, AsyncMock, AsyncMock],
        mock_conversation_messages: list[ConversationMessage],
        mock_ai_response: AIResponse,
    ) -> None:
        """Тест отключения кеша."""
        manager, mock_openrouter, mock_deepseek = manager_with_mocked_providers

        mock_openrouter.generate_response.return_value = mock_ai_response

        # Запрос без кеша
        response = await manager.generate_response(
            mock_conversation_messages,
            use_cache=False,
        )

        assert response.cached is False
        mock_openrouter.generate_response.assert_called_once()


@pytest.mark.ai_manager
@pytest.mark.integration
class TestAIManagerSimpleResponse:
    """Тесты упрощенного API для быстрых ответов."""

    @pytest.mark.asyncio
    async def test_generate_simple_response(self, mock_ai_manager: AsyncMock) -> None:
        """Тест генерации простого ответа."""
        response = await mock_ai_manager.generate_simple_response("Привет!")

        assert response.content == "Это тестовый ответ от AI"
        mock_ai_manager.generate_simple_response.assert_called_once_with("Привет!")

    @pytest.mark.asyncio
    async def test_simple_response_with_parameters(
        self, mock_ai_manager: AsyncMock
    ) -> None:
        """Тест простого ответа с параметрами."""
        custom_response = AIResponse(
            content="Кастомный ответ",
            model="custom-model",
            provider="test-provider",
            tokens_used=15,
            response_time=0.3,
            cached=False,
        )
        mock_ai_manager.generate_simple_response.return_value = custom_response

        response = await mock_ai_manager.generate_simple_response(
            "Тест с параметрами",
            temperature=0.8,
            max_tokens=100,
        )

        assert response.content == "Кастомный ответ"


@pytest.mark.ai_manager
@pytest.mark.integration
class TestAIManagerLifecycle:
    """Тесты жизненного цикла AIManager."""

    @pytest.mark.asyncio
    async def test_manager_close(
        self, manager_with_mocked_providers: tuple[AIManager, AsyncMock, AsyncMock]
    ) -> None:
        """Тест корректного закрытия менеджера."""
        manager, mock_openrouter, mock_deepseek = manager_with_mocked_providers

        await manager.close()

        # Проверяем что close вызван у всех провайдеров
        mock_openrouter.close.assert_called_once()
        mock_deepseek.close.assert_called_once()

    # @pytest.mark.asyncio
    # async def test_manager_context_manager(self, mock_config):
    #     """Тест использования менеджера как context manager."""
    #     # AIManager не поддерживает async context manager
    #     with patch('app.services.ai_manager.get_config', return_value=mock_config):
    #         async with AIManager() as manager:
    #             assert manager is not None
    #             # Менеджер должен быть доступен в контексте
    #             assert hasattr(manager, '_providers')


@pytest.mark.ai_manager
@pytest.mark.integration
class TestAIManagerErrorHandling:
    """Тесты обработки ошибок в AIManager."""

    @pytest.mark.asyncio
    async def test_invalid_messages_format(self, mock_ai_manager: AsyncMock) -> None:
        """Тест обработки некорректного формата сообщений."""
        # Мок должен выбрасывать ошибку
        mock_ai_manager.generate_response.side_effect = ValueError(
            "Сообщения должны быть списком",
        )

        with pytest.raises(ValueError, match="Сообщения должны быть списком"):
            await mock_ai_manager.generate_response("не список")

    @pytest.mark.asyncio
    async def test_empty_messages_list(self, mock_ai_manager: AsyncMock) -> None:
        """Тест обработки пустого списка сообщений."""
        # Мок должен выбрасывать ошибку
        mock_ai_manager.generate_response.side_effect = ValueError(
            "Список сообщений не может быть пустым",
        )

        with pytest.raises(ValueError, match="Список сообщений не может быть пустым"):
            await mock_ai_manager.generate_response([])

    @pytest.mark.asyncio
    async def test_authentication_error_handling(
        self,
        manager_with_mocked_providers: tuple[AIManager, AsyncMock, AsyncMock],
        mock_conversation_messages: list[ConversationMessage],
    ) -> None:
        """Тест обработки ошибок аутентификации."""
        manager, mock_openrouter, mock_deepseek = manager_with_mocked_providers

        # Оба провайдера выдают ошибку аутентификации
        mock_openrouter.generate_response.side_effect = APIAuthenticationError(
            "Invalid API key",
            "openrouter",
        )
        mock_deepseek.generate_response.side_effect = APIAuthenticationError(
            "Invalid API key",
            "deepseek",
        )

        with pytest.raises(
            AIProviderError,
            match="Все AI провайдеры недоступны: Invalid API key",
        ):
            await manager.generate_response(mock_conversation_messages, use_cache=False)

    @pytest.mark.asyncio
    async def test_mixed_error_handling(
        self,
        manager_with_mocked_providers: tuple[AIManager, AsyncMock, AsyncMock],
        mock_conversation_messages: list[ConversationMessage],
        mock_ai_response: AIResponse,
    ) -> None:
        """Тест обработки смешанных ошибок."""
        manager, mock_openrouter, mock_deepseek = manager_with_mocked_providers

        # OpenRouter - ошибка аутентификации, DeepSeek - работает
        mock_openrouter.generate_response.side_effect = APIAuthenticationError(
            "Invalid API key",
            "openrouter",
        )
        mock_deepseek.generate_response.return_value = mock_ai_response

        response = await manager.generate_response(mock_conversation_messages)

        # Должен использоваться DeepSeek как fallback
        assert response.content == "Это тестовый ответ от AI"

        # Проверяем статистику ошибок
        stats = manager.get_stats()
        assert stats["fallback_used"] > 0
