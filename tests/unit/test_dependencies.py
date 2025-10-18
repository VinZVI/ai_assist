"""
Тесты для системы dependency injection.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from app.core.dependencies import DependencyContainer


class TestDependencyContainer:
    """Тесты для контейнера зависимостей."""

    def test_register_and_get_singleton(self):
        """Тест регистрации и получения singleton сервиса."""
        container = DependencyContainer()

        # Создаем mock сервис
        mock_service = Mock()
        mock_service.name = "test_service"

        # Регистрируем singleton
        container.register_singleton("test_service", mock_service)

        # Получаем сервис дважды
        service1 = container.get("test_service")
        service2 = container.get("test_service")

        # Проверяем, что это один и тот же объект
        assert service1 is service2
        assert service1.name == "test_service"

    def test_register_and_get_factory(self):
        """Тест регистрации и получения сервиса через factory."""
        container = DependencyContainer()

        # Создаем factory
        call_count = 0

        def service_factory():
            nonlocal call_count
            call_count += 1
            mock_service = Mock()
            mock_service.name = f"factory_service_{call_count}"
            return mock_service

        # Регистрируем factory
        container.register_factory("factory_service", service_factory)

        # Получаем сервис - первый вызов создает и сохраняет сервис
        service1 = container.get("factory_service")

        # Получаем сервис снова - должен вернуть тот же экземпляр (кэширование)
        service2 = container.get("factory_service")

        # Проверяем, что это один и тот же объект (factory вызван только один раз)
        assert service1 is service2
        assert service1.name == "factory_service_1"
        assert call_count == 1  # Factory был вызван только один раз

    def test_get_nonexistent_service_raises_error(self):
        """Тест получения несуществующего сервиса вызывает ошибку."""
        container = DependencyContainer()

        with pytest.raises(
            ValueError, match="Service 'nonexistent' not found in container"
        ):
            container.get("nonexistent")

    @pytest.mark.asyncio
    async def test_get_async_service_with_initialization(self):
        """Тест асинхронного получения сервиса с инициализацией."""
        container = DependencyContainer()

        # Создаем mock сервис с методом initialize
        mock_service = Mock()
        mock_service._initialized = False
        mock_service.initialize = AsyncMock()

        container.register_singleton("async_service", mock_service)

        # Получаем сервис асинхронно
        retrieved_service = await container.get_async("async_service")

        # Проверяем, что initialize был вызван
        mock_service.initialize.assert_called_once()
        assert retrieved_service._initialized is True

        # Повторный вызов не должен вызывать initialize снова
        mock_service.initialize.reset_mock()
        await container.get_async("async_service")
        mock_service.initialize.assert_not_called()
