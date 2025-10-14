"""
Тесты для AntiSpamMiddleware и MessageCountingMiddleware.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, Message, User

from app.middleware.anti_spam import AntiSpamMiddleware
from app.middleware.message_counter import MessageCountingMiddleware
from app.models.user import User as UserModel


class TestAntiSpamMiddleware:
    """Тесты для AntiSpamMiddleware."""

    @pytest.fixture
    def anti_spam_middleware(self) -> AntiSpamMiddleware:
        """Фикстура для AntiSpamMiddleware."""
        return AntiSpamMiddleware()

    @pytest.fixture
    def mock_message_event(self) -> MagicMock:
        """Фикстура для мокированного сообщения."""
        event = MagicMock(spec=Message)
        event.from_user = MagicMock(spec=User)
        event.from_user.id = 12345
        event.from_user.username = "testuser"
        event.answer = AsyncMock()
        event.text = "Test message"
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
    async def test_anti_spam_middleware_under_limit_message(
        self, anti_spam_middleware: AntiSpamMiddleware, mock_message_event: MagicMock
    ) -> None:
        """Тест обработки сообщения в пределах лимита."""
        # Arrange
        mock_handler = AsyncMock()
        mock_data = {}

        # Act
        await anti_spam_middleware(mock_handler, mock_message_event, mock_data)

        # Assert
        mock_handler.assert_called_once_with(mock_message_event, mock_data)
        mock_message_event.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_anti_spam_middleware_over_limit_message(
        self, anti_spam_middleware: AntiSpamMiddleware, mock_message_event: MagicMock
    ) -> None:
        """Тест обработки сообщения при превышении лимита."""
        # Arrange
        mock_handler = AsyncMock()
        mock_data = {}

        # Fill up the action count to reach the limit (20 by default)
        user_id = mock_message_event.from_user.id
        for _ in range(20):
            anti_spam_middleware._user_actions[user_id].append(datetime.now(UTC))

        # Act
        result = await anti_spam_middleware(mock_handler, mock_message_event, mock_data)

        # Assert
        assert result is None  # Handler should not be called
        mock_handler.assert_not_called()
        mock_message_event.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_anti_spam_middleware_over_limit_callback(
        self, anti_spam_middleware: AntiSpamMiddleware, mock_callback_event: MagicMock
    ) -> None:
        """Тест обработки callback запроса при превышении лимита."""
        # Arrange
        mock_handler = AsyncMock()
        mock_data = {}

        # Fill up the action count to reach the limit (20 by default)
        user_id = mock_callback_event.from_user.id
        for _ in range(20):
            anti_spam_middleware._user_actions[user_id].append(datetime.now(UTC))

        # Act
        result = await anti_spam_middleware(mock_handler, mock_callback_event, mock_data)

        # Assert
        assert result is None  # Handler should not be called
        mock_handler.assert_not_called()
        mock_callback_event.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_anti_spam_middleware_user_blocked(
        self, anti_spam_middleware: AntiSpamMiddleware, mock_message_event: MagicMock
    ) -> None:
        """Тест обработки сообщения от заблокированного пользователя."""
        # Arrange
        mock_handler = AsyncMock()
        mock_data = {}

        # Set user as blocked
        user_id = mock_message_event.from_user.id
        anti_spam_middleware._user_blocks[user_id] = datetime.now(UTC) + timedelta(seconds=10)

        # Act
        result = await anti_spam_middleware(mock_handler, mock_message_event, mock_data)

        # Assert
        assert result is None  # Handler should not be called
        mock_handler.assert_not_called()
        mock_message_event.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_anti_spam_middleware_user_block_expired(
        self, anti_spam_middleware: AntiSpamMiddleware, mock_message_event: MagicMock
    ) -> None:
        """Тест обработки сообщения от пользователя с истекшей блокировкой."""
        # Arrange
        mock_handler = AsyncMock()
        mock_data = {}
        mock_user = MagicMock(spec=UserModel)
        mock_user.language_code = "ru"
        mock_data["user"] = mock_user

        # Set user as blocked with expired time
        user_id = mock_message_event.from_user.id
        expired_time = datetime.now(UTC) - timedelta(seconds=10)
        anti_spam_middleware._user_blocks[user_id] = expired_time

        # Act
        result = await anti_spam_middleware(mock_handler, mock_message_event, mock_data)

        # Assert - when block expires, the user should be able to perform actions again
        # The middleware should process the action normally
        mock_handler.assert_called_once_with(mock_message_event, mock_data)
        mock_message_event.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_anti_spam_middleware_admin_user(
        self, anti_spam_middleware: AntiSpamMiddleware, mock_message_event: MagicMock
    ) -> None:
        """Тест обработки сообщения от администратора (без ограничений)."""
        # Arrange
        mock_handler = AsyncMock()
        mock_data = {"is_admin": True}

        # Fill up the action count beyond the limit
        user_id = mock_message_event.from_user.id
        for _ in range(50):  # Well above the default limit of 20
            anti_spam_middleware._user_actions[user_id].append(datetime.now(UTC))

        # Act
        await anti_spam_middleware(mock_handler, mock_message_event, mock_data)

        # Assert - admin should not be limited
        mock_handler.assert_called_once_with(mock_message_event, mock_data)
        mock_message_event.answer.assert_not_called()


class TestMessageCountingMiddleware:
    """Тесты для MessageCountingMiddleware."""

    @pytest.fixture
    def message_counting_middleware(self) -> MessageCountingMiddleware:
        """Фикстура для MessageCountingMiddleware."""
        return MessageCountingMiddleware()

    @pytest.fixture
    def mock_message_event(self) -> MagicMock:
        """Фикстура для мокированного сообщения."""
        event = MagicMock(spec=Message)
        event.from_user = MagicMock(spec=User)
        event.from_user.id = 12345
        event.from_user.username = "testuser"
        event.answer = AsyncMock()
        event.text = "Test message"
        return event

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        """Фикстура для мокированного пользователя."""
        user = MagicMock(spec=UserModel)
        user.id = 1
        user.telegram_id = 12345
        user.username = "testuser"
        user.is_premium = False
        user.is_premium_active.return_value = False
        user.daily_message_count = 5
        user.last_message_date = datetime.now(UTC).date()
        return user

    @pytest.mark.asyncio
    async def test_message_counting_middleware_under_limit(
        self, message_counting_middleware: MessageCountingMiddleware, 
        mock_message_event: MagicMock, mock_user: MagicMock
    ) -> None:
        """Тест обработки сообщения в пределах дневного лимита."""
        # Arrange
        mock_handler = AsyncMock()
        mock_data = {"user": mock_user}

        with patch("app.middleware.message_counter.get_config") as mock_get_config, \
             patch("app.middleware.message_counter.get_session") as mock_get_session:
            
            # Mock config
            mock_config = MagicMock()
            mock_config.user_limits.daily_message_limit = 20
            mock_config.conversation.enable_saving = True
            mock_get_config.return_value = mock_config

            # Mock session
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Act
            await message_counting_middleware(mock_handler, mock_message_event, mock_data)

            # Assert
            mock_handler.assert_called_once_with(mock_message_event, mock_data)
            mock_message_event.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_message_counting_middleware_over_limit(
        self, message_counting_middleware: MessageCountingMiddleware, 
        mock_message_event: MagicMock, mock_user: MagicMock
    ) -> None:
        """Тест обработки сообщения при превышении дневного лимита."""
        # Arrange
        mock_handler = AsyncMock()
        mock_data = {"user": mock_user}
        mock_user.daily_message_count = 20  # At limit

        with patch("app.middleware.message_counter.get_config") as mock_get_config:
            
            # Mock config
            mock_config = MagicMock()
            mock_config.user_limits.daily_message_limit = 20
            mock_config.conversation.enable_saving = True
            mock_get_config.return_value = mock_config

            # Act
            result = await message_counting_middleware(mock_handler, mock_message_event, mock_data)

            # Assert
            assert result is None  # Handler should not be called
            mock_handler.assert_not_called()
            mock_message_event.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_message_counting_middleware_premium_user(
        self, message_counting_middleware: MessageCountingMiddleware, 
        mock_message_event: MagicMock, mock_user: MagicMock
    ) -> None:
        """Тест обработки сообщения от премиум пользователя."""
        # Arrange
        mock_handler = AsyncMock()
        mock_data = {"user": mock_user}
        mock_user.is_premium = True
        mock_user.is_premium_active.return_value = True
        mock_user.daily_message_count = 100  # Over limit but should be allowed for premium

        with patch("app.middleware.message_counter.get_config") as mock_get_config:
            
            # Mock config
            mock_config = MagicMock()
            mock_config.user_limits.daily_message_limit = 20
            mock_config.conversation.enable_saving = True
            mock_get_config.return_value = mock_config

            # Act
            await message_counting_middleware(mock_handler, mock_message_event, mock_data)

            # Assert
            mock_handler.assert_called_once_with(mock_message_event, mock_data)
            mock_message_event.answer.assert_not_called()