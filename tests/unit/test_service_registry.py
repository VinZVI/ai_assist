"""
Тесты для реестра сервисов.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.core.service_registry import (
    initialize_services,
    _initialize_monitoring_services,
)


class TestServiceRegistry:
    """Тесты для реестра сервисов."""

    @pytest.mark.asyncio
    async def test_initialize_monitoring_services(self):
        """Тест инициализации сервисов мониторинга."""
        # Пока просто проверяем, что функция не вызывает ошибок
        await _initialize_monitoring_services()

    @pytest.mark.asyncio
    async def test_initialize_services(self):
        """Тест полной инициализации сервисов."""
        with (
            patch("app.core.service_registry._initialize_database_services") as mock_db,
            patch("app.core.service_registry._initialize_cache_services") as mock_cache,
            patch(
                "app.core.service_registry._initialize_business_services"
            ) as mock_business,
            patch(
                "app.core.service_registry._initialize_monitoring_services"
            ) as mock_monitoring,
        ):
            # Настраиваем mocks
            mock_db.return_value = None
            mock_cache.return_value = None
            mock_business.return_value = None
            mock_monitoring.return_value = None

            # Вызываем тестируемую функцию
            await initialize_services()

            # Проверяем, что все функции инициализации были вызваны
            mock_db.assert_called_once()
            mock_cache.assert_called_once()
            mock_business.assert_called_once()
            mock_monitoring.assert_called_once()
