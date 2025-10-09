"""
Тесты для middleware компонентов.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, Message, User

from app.middleware.auth import AuthMiddleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.metrics import MetricsMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.models.user import User as UserModel


class TestAuthMiddleware:
    """Тесты для AuthMiddleware."""

    @pytest.fixture
    def auth_middleware(self) -> AuthMiddleware:
        """Фикстура для AuthMiddleware."""
        return AuthMiddleware()

    @pytest.fixture
    def mock_event(self) -> MagicMock:
        """Фикстура для мокированного события."""
        event = MagicMock()
        event.from_user = MagicMock(spec=User)
        event.from_user.id = 12345
        event.from_user.username = "testuser"
        return event

    @pytest.mark.asyncio
    async def test_auth_middleware_success(
        self, auth_middleware: AuthMiddleware, mock_event: MagicMock
    ) -> None:
        """Тест успешной аутентификации пользователя."""
        # Arrange
        mock_handler = AsyncMock()
        mock_data = {}

        # Mock user service
        mock_user = MagicMock(spec=UserModel)
        mock_user.id = 1
        mock_user.username = "testuser"

        with pytest.MonkeyPatch().context() as m:
            m.setattr(
                "app.middleware.auth.get_or_update_user",
                AsyncMock(return_value=mock_user),
            )

            # Act
            await auth_middleware(mock_handler, mock_event, mock_data)

            # Assert
            mock_handler.assert_called_once_with(mock_event, mock_data)
            assert "user" in mock_data
            assert mock_data["user"] == mock_user

    @pytest.mark.asyncio
    async def test_auth_middleware_no_user(
        self, auth_middleware: AuthMiddleware
    ) -> None:
        """Тест аутентификации при отсутствии пользователя в событии."""
        # Arrange
        mock_handler = AsyncMock()
        mock_data = {}
        event = MagicMock()
        event.from_user = None

        # Act
        await auth_middleware(mock_handler, event, mock_data)

        # Assert
        mock_handler.assert_called_once_with(event, mock_data)
        assert "user" not in mock_data

    @pytest.mark.asyncio
    async def test_auth_middleware_exception_handling(
        self, auth_middleware: AuthMiddleware, mock_event: MagicMock
    ) -> None:
        """Тест обработки исключений в аутентификации."""
        # Arrange
        mock_handler = AsyncMock()
        mock_data = {}

        with pytest.MonkeyPatch().context() as m:
            m.setattr(
                "app.middleware.auth.get_or_update_user",
                AsyncMock(side_effect=Exception("Test error")),
            )

            # Act
            await auth_middleware(mock_handler, mock_event, mock_data)

            # Assert
            mock_handler.assert_called_once_with(mock_event, mock_data)
            assert "user" not in mock_data


class TestRateLimitMiddleware:
    """Тесты для RateLimitMiddleware."""

    @pytest.fixture
    def rate_limit_middleware(self) -> RateLimitMiddleware:
        """Фикстура для RateLimitMiddleware."""
        return RateLimitMiddleware(requests_per_minute=5)

    @pytest.fixture
    def mock_message_event(self) -> MagicMock:
        """Фикстура для мокированного сообщения."""
        event = MagicMock(spec=Message)
        event.from_user = MagicMock(spec=User)
        event.from_user.id = 12345
        event.from_user.username = "testuser"
        event.answer = AsyncMock()
        return event

    @pytest.fixture
    def mock_callback_event(self) -> MagicMock:
        """Фикстура для мокированного callback запроса."""
        event = MagicMock(spec=CallbackQuery)
        event.from_user = MagicMock(spec=User)
        event.from_user.id = 12345
        event.from_user.username = "testuser"
        event.answer = AsyncMock()
        return event

    @pytest.mark.asyncio
    async def test_rate_limit_middleware_under_limit_message(
        self, rate_limit_middleware: RateLimitMiddleware, mock_message_event: MagicMock
    ) -> None:
        """Тест обработки сообщения в пределах лимита."""
        # Arrange
        mock_handler = AsyncMock()
        mock_data = {}

        # Act
        await rate_limit_middleware(mock_handler, mock_message_event, mock_data)

        # Assert
        mock_handler.assert_called_once_with(mock_message_event, mock_data)
        mock_message_event.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_rate_limit_middleware_over_limit_message(
        self, rate_limit_middleware: RateLimitMiddleware, mock_message_event: MagicMock
    ) -> None:
        """Тест обработки сообщения при превышении лимита."""
        # Arrange
        mock_handler = AsyncMock()
        mock_data = {}

        # Fill up the request count to reach the limit
        user_id = mock_message_event.from_user.id
        for _ in range(5):
            rate_limit_middleware._request_counts[user_id].append(datetime.now(UTC))

        # Act
        result = await rate_limit_middleware(
            mock_handler, mock_message_event, mock_data
        )

        # Assert
        assert result is None  # Handler should not be called
        mock_handler.assert_not_called()
        mock_message_event.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limit_middleware_over_limit_callback(
        self, rate_limit_middleware: RateLimitMiddleware, mock_callback_event: MagicMock
    ) -> None:
        """Тест обработки callback запроса при превышении лимита."""
        # Arrange
        mock_handler = AsyncMock()
        mock_data = {}

        # Fill up the request count to reach the limit
        user_id = mock_callback_event.from_user.id
        for _ in range(5):
            rate_limit_middleware._request_counts[user_id].append(datetime.now(UTC))

        # Act
        result = await rate_limit_middleware(
            mock_handler, mock_callback_event, mock_data
        )

        # Assert
        assert result is None  # Handler should not be called
        mock_handler.assert_not_called()
        mock_callback_event.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limit_middleware_no_user(
        self, rate_limit_middleware: RateLimitMiddleware
    ) -> None:
        """Тест ограничения частоты при отсутствии пользователя."""
        # Arrange
        mock_handler = AsyncMock()
        mock_data = {}
        event = MagicMock()
        event.from_user = None

        # Act
        await rate_limit_middleware(mock_handler, event, mock_data)

        # Assert
        mock_handler.assert_called_once_with(event, mock_data)

    def test_rate_limit_stats(self, rate_limit_middleware: RateLimitMiddleware) -> None:
        """Тест получения статистики ограничения частоты."""
        # Arrange
        rate_limit_middleware._rate_limit_stats["requests_limited"] = 5
        rate_limit_middleware._rate_limit_stats["users_limited"] = 2

        # Act
        stats = rate_limit_middleware.get_rate_limit_stats()

        # Assert
        assert stats["requests_limited"] == 5
        assert stats["users_limited"] == 2

        # Test reset
        rate_limit_middleware.reset_rate_limit_stats()
        stats = rate_limit_middleware.get_rate_limit_stats()
        assert stats["requests_limited"] == 0
        assert stats["users_limited"] == 0

    @pytest.mark.asyncio
    async def test_rate_limit_middleware_premium_user(
        self, rate_limit_middleware: RateLimitMiddleware, mock_message_event: MagicMock
    ) -> None:
        """Тест обработки запроса от премиум пользователя."""
        # Arrange
        mock_handler = AsyncMock()
        mock_user = MagicMock(spec=UserModel)
        mock_user.is_premium = True
        mock_data = {"user": mock_user}

        # Fill up the request count to reach the normal limit but should be allowed for premium
        user_id = mock_message_event.from_user.id
        for _ in range(5):
            rate_limit_middleware._request_counts[user_id].append(datetime.now(UTC))

        # Act
        await rate_limit_middleware(mock_handler, mock_message_event, mock_data)

        # Assert
        mock_handler.assert_called_once_with(mock_message_event, mock_data)
        mock_message_event.answer.assert_not_called()


class TestLoggingMiddleware:
    """Тесты для LoggingMiddleware."""

    @pytest.fixture
    def logging_middleware(self) -> LoggingMiddleware:
        """Фикстура для LoggingMiddleware."""
        return LoggingMiddleware()

    @pytest.fixture
    def mock_message_event(self) -> MagicMock:
        """Фикстура для мокированного сообщения."""
        event = MagicMock(spec=Message)
        event.from_user = MagicMock(spec=User)
        event.from_user.id = 12345
        event.from_user.username = "testuser"
        event.message_id = 100
        event.chat = MagicMock()
        event.chat.id = 500
        event.text = "Test message"
        return event

    @pytest.fixture
    def mock_callback_event(self) -> MagicMock:
        """Фикстура для мокированного callback запроса."""
        event = MagicMock(spec=CallbackQuery)
        event.from_user = MagicMock(spec=User)
        event.from_user.id = 12345
        event.from_user.username = "testuser"
        event.id = "callback_1"
        event.data = "test_callback"
        event.message = MagicMock()
        event.message.message_id = 200
        return event

    @pytest.mark.asyncio
    async def test_logging_middleware_message(
        self, logging_middleware: LoggingMiddleware, mock_message_event: MagicMock
    ) -> None:
        """Тест логирования сообщения."""
        # Arrange
        mock_handler = AsyncMock()
        mock_data = {}

        # Act
        await logging_middleware(mock_handler, mock_message_event, mock_data)

        # Assert
        mock_handler.assert_called_once_with(mock_message_event, mock_data)

    @pytest.mark.asyncio
    async def test_logging_middleware_callback(
        self, logging_middleware: LoggingMiddleware, mock_callback_event: MagicMock
    ) -> None:
        """Тест логирования callback запроса."""
        # Arrange
        mock_handler = AsyncMock()
        mock_data = {}

        # Act
        await logging_middleware(mock_handler, mock_callback_event, mock_data)

        # Assert
        mock_handler.assert_called_once_with(mock_callback_event, mock_data)

    @pytest.mark.asyncio
    async def test_logging_middleware_exception_handling(
        self, logging_middleware: LoggingMiddleware, mock_message_event: MagicMock
    ) -> None:
        """Тест обработки исключений в логировании."""
        # Arrange
        mock_handler = AsyncMock(side_effect=Exception("Test error"))
        mock_data = {}

        # Act & Assert
        with pytest.raises(Exception, match="Test error"):
            await logging_middleware(mock_handler, mock_message_event, mock_data)

    def test_logging_stats(self, logging_middleware: LoggingMiddleware) -> None:
        """Тест получения статистики логирования."""
        # Arrange
        logging_middleware._logging_stats["messages_logged"] = 3
        logging_middleware._logging_stats["callbacks_logged"] = 2
        logging_middleware._logging_stats["other_events_logged"] = 1

        # Act
        stats = logging_middleware.get_logging_stats()

        # Assert
        assert stats["messages_logged"] == 3
        assert stats["callbacks_logged"] == 2
        assert stats["other_events_logged"] == 1

        # Test reset
        logging_middleware.reset_logging_stats()
        stats = logging_middleware.get_logging_stats()
        assert stats["messages_logged"] == 0
        assert stats["callbacks_logged"] == 0
        assert stats["other_events_logged"] == 0


class TestMetricsMiddleware:
    """Тесты для MetricsMiddleware."""

    @pytest.fixture
    def metrics_middleware(self) -> MetricsMiddleware:
        """Фикстура для MetricsMiddleware."""
        return MetricsMiddleware()

    @pytest.fixture
    def mock_message_event(self) -> MagicMock:
        """Фикстура для мокированного сообщения."""
        event = MagicMock(spec=Message)
        event.from_user = MagicMock(spec=User)
        event.from_user.id = 12345
        event.from_user.username = "testuser"
        return event

    @pytest.fixture
    def mock_callback_event(self) -> MagicMock:
        """Фикстура для мокированного callback запроса."""
        event = MagicMock(spec=CallbackQuery)
        event.from_user = MagicMock(spec=User)
        event.from_user.id = 12345
        event.from_user.username = "testuser"
        return event

    @pytest.mark.asyncio
    async def test_metrics_middleware_message(
        self, metrics_middleware: MetricsMiddleware, mock_message_event: MagicMock
    ) -> None:
        """Тест сбора метрик для сообщения."""
        # Arrange
        initial_requests = metrics_middleware.get_usage_metrics()["total_requests"]
        mock_handler = AsyncMock()
        mock_data = {}

        # Act
        await metrics_middleware(mock_handler, mock_message_event, mock_data)

        # Assert
        mock_handler.assert_called_once_with(mock_message_event, mock_data)
        updated_metrics = metrics_middleware.get_usage_metrics()
        assert updated_metrics["total_requests"] == initial_requests + 1
        assert updated_metrics["message_requests"] == 1

    @pytest.mark.asyncio
    async def test_metrics_middleware_callback(
        self, metrics_middleware: MetricsMiddleware, mock_callback_event: MagicMock
    ) -> None:
        """Тест сбора метрик для callback запроса."""
        # Arrange
        initial_requests = metrics_middleware.get_usage_metrics()["total_requests"]
        mock_handler = AsyncMock()
        mock_data = {}

        # Act
        await metrics_middleware(mock_handler, mock_callback_event, mock_data)

        # Assert
        mock_handler.assert_called_once_with(mock_callback_event, mock_data)
        updated_metrics = metrics_middleware.get_usage_metrics()
        assert updated_metrics["total_requests"] == initial_requests + 1
        assert updated_metrics["callback_requests"] == 1

    def test_metrics_middleware_get_usage_metrics(
        self, metrics_middleware: MetricsMiddleware
    ) -> None:
        """Тест получения метрик использования."""
        # Arrange
        metrics_middleware._metrics["total_requests"] = 10
        metrics_middleware._metrics["message_requests"] = 7
        metrics_middleware._metrics["callback_requests"] = 3
        metrics_middleware._metrics["user_requests"][12345] = 5
        metrics_middleware._metrics["user_requests"][67890] = 3

        # Act
        metrics = metrics_middleware.get_usage_metrics()

        # Assert
        assert metrics["total_requests"] == 10
        assert metrics["message_requests"] == 7
        assert metrics["callback_requests"] == 3
        assert metrics["other_requests"] == 0
        assert metrics["unique_users"] == 2
        assert metrics["requests_per_user"][12345] == 5
        assert metrics["requests_per_user"][67890] == 3

    def test_metrics_middleware_reset_metrics(
        self, metrics_middleware: MetricsMiddleware
    ) -> None:
        """Тест сброса метрик."""
        # Arrange
        metrics_middleware._metrics["total_requests"] = 10
        metrics_middleware._metrics["user_requests"][12345] = 5

        # Act
        metrics_middleware.reset_metrics()
        metrics = metrics_middleware.get_usage_metrics()

        # Assert
        assert metrics["total_requests"] == 0
        assert metrics["unique_users"] == 0
