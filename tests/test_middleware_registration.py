"""
Тест для проверки регистрации middleware без дублирования логов
"""

from unittest.mock import MagicMock, patch

import pytest
from aiogram import Dispatcher


def test_middleware_registration():
    """Тест регистрации middleware без дублирования логов."""
    # Патчим logger.info чтобы отслеживать вызовы
    with (
        patch("app.middleware.logging.logger") as mock_logging_logger,
        patch("app.middleware.auth.logger") as mock_auth_logger,
        patch("app.middleware.rate_limit.logger") as mock_rate_limit_logger,
        patch("app.middleware.metrics.logger") as mock_metrics_logger,
    ):
        # Теперь импортируем middleware классы после патчинга
        from app.middleware.auth import AuthMiddleware
        from app.middleware.logging import LoggingMiddleware
        from app.middleware.metrics import MetricsMiddleware
        from app.middleware.rate_limit import RateLimitMiddleware

        # Создаем диспетчер
        dp = Dispatcher()

        # Создаем единственные экземпляры middleware
        logging_middleware = LoggingMiddleware()
        auth_middleware = AuthMiddleware()
        rate_limit_middleware = RateLimitMiddleware()
        metrics_middleware = MetricsMiddleware()

        # Регистрируем middleware для message и callback_query
        dp.message.middleware(logging_middleware)
        dp.callback_query.middleware(logging_middleware)

        dp.message.middleware(auth_middleware)
        dp.callback_query.middleware(auth_middleware)

        dp.message.middleware(rate_limit_middleware)
        dp.callback_query.middleware(rate_limit_middleware)

        dp.message.middleware(metrics_middleware)
        dp.callback_query.middleware(metrics_middleware)

        # Проверяем, что каждый middleware был инициализирован только один раз
        # LoggingMiddleware
        mock_logging_logger.info.assert_called_once_with(
            "📝 LoggingMiddleware инициализирован"
        )

        # AuthMiddleware
        mock_auth_logger.info.assert_called_once_with(
            "🛡️ AuthMiddleware инициализирован"
        )

        # RateLimitMiddleware
        mock_rate_limit_logger.info.assert_called_once()

        # MetricsMiddleware
        mock_metrics_logger.info.assert_called_once_with(
            "📊 MetricsMiddleware инициализирован"
        )
