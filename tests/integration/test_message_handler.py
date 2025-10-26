"""
Тесты для обработчика сообщений (message handler).

Этот модуль содержит комплексные тесты для проверки функциональности
обработчика текстовых сообщений, включая:
- Проверку регистрации пользователей
- Валидацию сообщений
- Проверку лимитов
- Интеграцию с AI сервисом
- Сохранение диалогов
- Обработку ошибок
"""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import Bot
from aiogram.types import Chat, Message
from aiogram.types import User as TelegramUser
from app.services.conversation_service import get_recent_conversation_history
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import AppConfig
from app.handlers.message import (
    create_system_message,
    generate_ai_response,
    handle_text_message,
    sanitize_telegram_message,  # Add the import for our new function
    save_conversation,
)
from app.models.conversation import Conversation, ConversationStatus, MessageRole
from app.models.user import User
from app.services.ai_manager import AIProviderError
from app.services.ai_providers.base import AIResponse, ConversationMessage
from app.services.user_service import get_or_update_user


class TestGetOrUpdateUser:
    """Тесты функции get_or_update_user."""

    @pytest.fixture
    def mock_message(self) -> MagicMock:
        """Создает мок объект сообщения."""
        message = MagicMock(spec=Message)
        message.from_user = MagicMock(spec=TelegramUser)
        message.from_user.id = 123456
        message.from_user.username = "testuser"
        message.from_user.first_name = "Test"
        message.from_user.last_name = "User"
        message.from_user.language_code = "en"
        message.chat = MagicMock(spec=Chat)
        message.chat.id = 789012
        message.text = "Hello, AI!"
        message.answer = AsyncMock()
        return message

    @pytest.fixture
    def mock_user(self) -> User:
        """Создает мок пользователя."""
        return User(
            telegram_id=123456,
            username="testuser",
            first_name="Test",
            last_name="User",
            daily_message_count=5,
            is_premium=False,
        )

    @pytest.mark.asyncio
    async def test_get_existing_user(self, mock_message: MagicMock) -> None:
        """Тест получения существующего пользователя."""
        # Arrange
        existing_user = User(
            id=1,
            telegram_id=123456,
            username="testuser",
            first_name="Test",
            last_name="User",
            daily_message_count=5,
            is_premium=False,
        )

        # Mock the session context manager
        mock_session_ctx = MagicMock()
        mock_session = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session

        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        with patch(
            "app.services.user_service.get_session", return_value=mock_session_ctx
        ):
            # Act
            result = await get_or_update_user(mock_message)

            # Assert
            assert result is not None
            assert result.telegram_id == 123456
            assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_user_not_found(self, mock_message: MagicMock) -> None:
        """Тест случая когда пользователь не найден."""
        # Mock the session context manager
        mock_session_ctx = MagicMock()
        mock_session = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session

        # Mock the query result - user not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Mock session.add and commit
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        # Mock refresh to set an ID on the user object
        async def mock_refresh(user: User) -> None:
            user.id = 1  # Simulate database setting the ID

        mock_session.refresh = mock_refresh

        with patch(
            "app.services.user_service.get_session", return_value=mock_session_ctx
        ):
            # Act
            result = await get_or_update_user(mock_message)

            # Assert
            assert result is not None  # Should create a new user
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_message_without_user(self) -> None:
        """Тест обработки сообщения без данных пользователя."""
        # Arrange
        message = MagicMock(spec=Message)
        message.from_user = None

        # Act
        result = await get_or_update_user(message)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_database_error(self, mock_message: MagicMock) -> None:
        """Тест обработки ошибки базы данных."""
        # Mock the session context manager to raise an exception
        mock_session_ctx = MagicMock()
        mock_session_ctx.__aenter__ = AsyncMock(side_effect=Exception("Database error"))
        mock_session_ctx.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "app.services.user_service.get_session", return_value=mock_session_ctx
        ):
            with patch("app.services.user_service.logger"):
                # Act
                result = await get_or_update_user(mock_message)

                # Assert
                assert result is None


class TestGetRecentConversationHistory:
    """Тесты функции get_recent_conversation_history."""

    @pytest.mark.asyncio
    async def test_get_conversation_history(self) -> None:
        """Тест получения истории диалогов."""
        # Arrange
        user_id = 12345
        conversations = [
            Conversation(
                id=1,
                user_id=user_id,
                message_text="Hello",
                response_text="Hi there!",
                role=MessageRole.USER,
                status=ConversationStatus.COMPLETED,
                created_at=datetime(2025, 9, 12, 10, 0, tzinfo=UTC),
            ),
        ]

        # Mock the session
        mock_session = AsyncMock()

        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = conversations
        mock_session.execute.return_value = mock_result

        # Act
        result = await get_recent_conversation_history(mock_session, user_id, limit=5)

        # Assert
        assert len(result) == 2
        # The order should be user message first, then assistant response
        assert result[0].role == "user"
        assert result[0].content == "Hello"
        assert result[1].role == "assistant"
        assert result[1].content == "Hi there!"

    @pytest.mark.asyncio
    async def test_empty_conversation_history(self) -> None:
        """Тест получения пустой истории диалогов."""
        # Mock the session
        mock_session = AsyncMock()

        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        # Act
        result = await get_recent_conversation_history(mock_session, 12345, limit=5)

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_conversation_history_database_error(self) -> None:
        """Тест обработки ошибки при получении истории."""
        # Mock the session
        mock_session = AsyncMock()

        # Mock the query to raise an exception
        mock_session.execute.side_effect = Exception("Database error")

        # Act
        result = await get_recent_conversation_history(mock_session, 12345, limit=5)

        # Assert
        assert result == []


class TestCreateSystemMessage:
    """Тесты функции create_system_message."""

    def test_create_system_message(self) -> None:
        """Тест создания системного сообщения."""
        # Act
        result = create_system_message()

        # Assert
        assert isinstance(result, ConversationMessage)
        assert result.role == "system"
        assert "эмпатичный AI-помощник" in result.content


class TestSaveConversation:
    """Тесты функции save_conversation."""

    @pytest.mark.asyncio
    async def test_save_conversation_success(self) -> None:
        """Тест успешного сохранения диалога."""
        # Arrange
        mock_session = AsyncMock()
        user_id = 12345
        user_message = "Hello, AI!"
        ai_response = "Hello, user!"
        ai_model = "test-model"
        tokens_used = 10
        response_time = 0.5

        mock_session.commit = AsyncMock()
        mock_session.add = MagicMock()

        # Act
        result = await save_conversation(
            session=mock_session,
            user_id=user_id,
            user_message=user_message,
            ai_response=ai_response,
            ai_model=ai_model,
            tokens_used=tokens_used,
            response_time=response_time,
        )

        # Assert
        assert result is True
        assert mock_session.add.call_count == 2  # Two conversations added
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_conversation_failure(self) -> None:
        """Тест неудачного сохранения диалога."""
        # Arrange
        mock_session = AsyncMock()
        user_id = 12345
        user_message = "Hello, AI!"
        ai_response = "Hello, user!"
        ai_model = "test-model"
        tokens_used = 10
        response_time = 0.5

        mock_session.commit = AsyncMock()
        mock_session.commit.side_effect = Exception("Database error")
        mock_session.rollback = AsyncMock()
        mock_session.add = MagicMock()

        # Act
        result = await save_conversation(
            session=mock_session,
            user_id=user_id,
            user_message=user_message,
            ai_response=ai_response,
            ai_model=ai_model,
            tokens_used=tokens_used,
            response_time=response_time,
        )

        # Assert
        assert result is False
        mock_session.rollback.assert_called_once()


class TestGenerateAiResponse:
    """Тесты функции generate_ai_response."""

    @pytest.mark.asyncio
    async def test_generate_ai_response_success(self) -> None:
        """Тест успешной генерации ответа от AI."""
        # Arrange
        mock_user = User(
            id=1,
            telegram_id=123456,
            username="testuser",
            first_name="Test",
            last_name="User",
            daily_message_count=5,
            is_premium=False,
        )
        user_message = "Hello, AI!"

        # Mock AI response
        mock_ai_response = AIResponse(
            content="Hello, user!",
            model="test-model",
            provider="test-provider",
            tokens_used=10,
            response_time=0.5,
        )

        with patch("app.handlers.message.get_ai_manager") as mock_get_ai_manager:
            mock_manager = AsyncMock()
            mock_get_ai_manager.return_value = mock_manager
            mock_manager.generate_response.return_value = mock_ai_response

            with patch(
                "app.handlers.message.get_recent_conversation_history"
            ) as mock_get_history:
                mock_get_history.return_value = []

                # Mock session context manager
                mock_session_ctx = MagicMock()
                mock_session = AsyncMock()
                mock_session_ctx.__aenter__.return_value = mock_session

                with patch(
                    "app.handlers.message.get_session", return_value=mock_session_ctx
                ):
                    # Act
                    result = await generate_ai_response(mock_user, user_message)

                    # Assert
                    assert len(result) == 4
                    assert result[0] == "Hello, user!"
                    assert result[1] == 10
                    assert result[2] == "test-model"
                    # The actual response_time calculation might be different due to execution time
                    # so we just check that it's a float
                    assert isinstance(result[3], float)

    @pytest.mark.asyncio
    async def test_generate_ai_response_api_error(self) -> None:
        """Тест генерации ответа при ошибке API."""
        # Arrange
        mock_user = User(
            id=1,
            telegram_id=123456,
            username="testuser",
            first_name="Test",
            last_name="User",
            daily_message_count=5,
            is_premium=False,
        )
        user_message = "Hello, AI!"

        with patch("app.handlers.message.get_ai_manager") as mock_get_ai_manager:
            mock_manager = AsyncMock()
            mock_get_ai_manager.return_value = mock_manager
            mock_manager.generate_response.side_effect = AIProviderError(
                "API error", "test-provider"
            )

            with patch(
                "app.handlers.message.get_recent_conversation_history"
            ) as mock_get_history:
                mock_get_history.return_value = []

                # Mock session context manager
                mock_session_ctx = MagicMock()
                mock_session = AsyncMock()
                mock_session_ctx.__aenter__.return_value = mock_session

                with patch(
                    "app.handlers.message.get_session", return_value=mock_session_ctx
                ):
                    # Act
                    result = await generate_ai_response(mock_user, user_message)

                    # Assert
                    assert len(result) == 4
                    assert (
                        "🤖 Возникла проблема с генерацией ответа. Попробуйте повторить сообщение."
                        in result[0]
                    )
                    assert result[1] == 0
                    assert result[2] == "fallback"
                    assert result[3] == 0.0

    @pytest.mark.asyncio
    async def test_generate_ai_response_unexpected_error(self) -> None:
        """Тест генерации ответа при неожиданной ошибке."""
        # Arrange
        mock_user = User(
            id=1,
            telegram_id=123456,
            username="testuser",
            first_name="Test",
            last_name="User",
            daily_message_count=5,
            is_premium=False,
        )
        user_message = "Hello, AI!"

        with patch("app.handlers.message.get_ai_manager") as mock_get_ai_manager:
            mock_manager = AsyncMock()
            mock_get_ai_manager.return_value = mock_manager
            mock_manager.generate_response.side_effect = Exception("Unexpected error")

            with patch(
                "app.handlers.message.get_recent_conversation_history"
            ) as mock_get_history:
                mock_get_history.return_value = []

                # Mock session context manager
                mock_session_ctx = MagicMock()
                mock_session = AsyncMock()
                mock_session_ctx.__aenter__.return_value = mock_session

                with patch(
                    "app.handlers.message.get_session", return_value=mock_session_ctx
                ):
                    # Act
                    result = await generate_ai_response(mock_user, user_message)

                    # Assert
                    assert len(result) == 4
                    assert (
                        "💥 Неожиданная ошибка при генерации ответа. Попробуйте позже."
                        in result[0]
                    )
                    assert result[1] == 0
                    assert result[2] == "error"
                    assert result[3] == 0.0


class TestHandleTextMessage:
    """Тесты функции handle_text_message."""

    @pytest.fixture
    def mock_telegram_message(self) -> MagicMock:
        """Создает мок Telegram сообщения."""
        message = MagicMock(spec=Message)
        message.from_user = MagicMock(spec=TelegramUser)
        message.from_user.id = 123456
        message.from_user.username = "testuser"
        message.from_user.first_name = "Test"
        message.from_user.last_name = "User"
        message.chat = MagicMock(spec=Chat)
        message.chat.id = 789012
        message.text = "Hello, AI!"
        message.answer = AsyncMock()
        message.bot = MagicMock(spec=Bot)
        message.bot.send_chat_action = AsyncMock()
        return message

    @pytest.mark.asyncio
    async def test_handle_text_message_success(
        self, mock_telegram_message: MagicMock, mock_config: AppConfig
    ) -> None:
        """Тест успешной обработки текстового сообщения."""
        # Arrange
        mock_user = User(
            id=1,
            telegram_id=123456,
            username="testuser",
            first_name="Test",
            last_name="User",
            daily_message_count=5,
            is_premium=False,
        )

        # Mock session context manager for conversation service
        mock_session_ctx_conv = MagicMock()
        mock_session_conv = AsyncMock()
        mock_session_ctx_conv.__aenter__.return_value = mock_session_conv

        # Create a mock save_conversation function to pass to the handler
        mock_save_conversation = AsyncMock(return_value=True)

        with patch(
            "app.handlers.message.generate_ai_response"
        ) as mock_generate_response:
            mock_generate_response.return_value = (
                "AI response",
                10,
                "test-model",
                0.5,
            )

            # Mock session context managers for conversation service
            with patch(
                "app.handlers.message.get_session",
                return_value=mock_session_ctx_conv,
            ):
                with patch(
                    "app.handlers.message.get_config",
                    return_value=mock_config,
                ):
                    # Act
                    await handle_text_message(
                        mock_telegram_message, mock_user, "ru", mock_save_conversation
                    )

                    # Assert
                    mock_generate_response.assert_called_once()
                    mock_save_conversation.assert_called_once()
                    mock_telegram_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_text_message_no_user_data(
        self, mock_telegram_message: MagicMock
    ) -> None:
        """Тест обработки сообщения без данных пользователя."""
        # Arrange
        mock_user = User(
            id=1,
            telegram_id=123456,
            username="testuser",
            first_name="Test",
            last_name="User",
            daily_message_count=5,
            is_premium=False,
        )

        # Act
        await handle_text_message(mock_telegram_message, mock_user)

        # Assert
        mock_telegram_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_text_message_too_short(
        self, mock_telegram_message: MagicMock
    ) -> None:
        """Тест обработки слишком короткого сообщения."""
        # Arrange
        mock_telegram_message.text = ""
        mock_user = User(
            id=1,
            telegram_id=123456,
            username="testuser",
            first_name="Test",
            last_name="User",
            daily_message_count=5,
            is_premium=False,
        )

        # Act
        await handle_text_message(mock_telegram_message, mock_user)

        # Assert
        mock_telegram_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_text_message_too_long(
        self, mock_telegram_message: MagicMock
    ) -> None:
        """Тест обработки слишком длинного сообщения."""
        # Arrange
        mock_telegram_message.text = "A" * 5000  # Too long message
        mock_user = User(
            id=1,
            telegram_id=123456,
            username="testuser",
            first_name="Test",
            last_name="User",
            daily_message_count=5,
            is_premium=False,
        )

        # Act
        await handle_text_message(mock_telegram_message, mock_user, "ru")

        # Assert
        mock_telegram_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_text_message_unregistered_user(
        self, mock_telegram_message: MagicMock
    ) -> None:
        """Тест обработки сообщения от незарегистрированного пользователя."""
        # Arrange
        mock_user = User(
            id=1,
            telegram_id=123456,
            username="testuser",
            first_name="Test",
            last_name="User",
            daily_message_count=5,
            is_premium=False,
        )

        # Act
        await handle_text_message(mock_telegram_message, mock_user)

        # Assert
        mock_telegram_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_text_message_limit_exceeded(
        self, mock_telegram_message: MagicMock
    ) -> None:
        """Тест обработки сообщения когда лимит исчерпан."""
        # Arrange
        mock_user = User(
            id=1,
            telegram_id=123456,
            username="testuser",
            first_name="Test",
            last_name="User",
            daily_message_count=100,  # Exceeds limit
            is_premium=False,
        )

        # Act
        await handle_text_message(mock_telegram_message, mock_user)

        # Assert
        mock_telegram_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_text_message_critical_error(
        self, mock_telegram_message: MagicMock
    ) -> None:
        """Тест обработки критической ошибки."""
        # Arrange
        mock_user = User(
            id=1,
            telegram_id=123456,
            username="testuser",
            first_name="Test",
            last_name="User",
            daily_message_count=5,
            is_premium=False,
        )

        with patch(
            "app.handlers.message.generate_ai_response"
        ) as mock_generate_response:
            mock_generate_response.side_effect = Exception("Critical error")

            # Act
            await handle_text_message(mock_telegram_message, mock_user)

            # Assert
            mock_telegram_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_text_message_with_special_characters_in_ai_response(
        self, mock_telegram_message: MagicMock, mock_config: AppConfig
    ) -> None:
        """Тест обработки сообщения с ответом AI, содержащим специальные символы."""
        # Arrange
        mock_user = User(
            id=1,
            telegram_id=123456,
            username="testuser",
            first_name="Test",
            last_name="User",
            daily_message_count=5,
            is_premium=False,
        )

        # Mock session context manager for conversation service
        mock_session_ctx_conv = MagicMock()
        mock_session_conv = AsyncMock()
        mock_session_ctx_conv.__aenter__.return_value = mock_session_conv

        # Create a mock save_conversation function to pass to the handler
        mock_save_conversation = AsyncMock(return_value=True)

        # Create an AI response with special characters that would cause Telegram parsing errors
        ai_response_with_special_chars = "Это ответ AI с ｜begin▁of▁sentence｜специальными символами｜end▁of▁sentence｜ которые вызывают ошибку в Telegram."

        with patch(
            "app.handlers.message.generate_ai_response"
        ) as mock_generate_response:
            mock_generate_response.return_value = (
                ai_response_with_special_chars,
                10,
                "test-model",
                0.5,
            )

            # Mock session context managers for conversation service
            with patch(
                "app.handlers.message.get_session",
                return_value=mock_session_ctx_conv,
            ):
                with patch(
                    "app.handlers.message.get_config",
                    return_value=mock_config,
                ):
                    # Act
                    await handle_text_message(
                        mock_telegram_message, mock_user, "ru", mock_save_conversation
                    )

                    # Assert
                    mock_generate_response.assert_called_once()
                    mock_save_conversation.assert_called_once()
                    # Check that the answer was called with the sanitized response
                    # The special characters should be removed
                    mock_telegram_message.answer.assert_called_once()
                    call_args = mock_telegram_message.answer.call_args[0][0]
                    assert "｜begin▁of▁sentence｜" not in call_args
                    assert "｜end▁of▁sentence｜" not in call_args


class TestMessageHandlerIntegration:
    """Интеграционные тесты обработчика сообщений."""

    @pytest.fixture
    def mock_telegram_message(self) -> MagicMock:
        """Создает мок Telegram сообщения."""
        message = MagicMock(spec=Message)
        message.from_user = MagicMock(spec=TelegramUser)
        message.from_user.id = 123456
        message.from_user.username = "testuser"
        message.from_user.first_name = "Test"
        message.from_user.last_name = "User"
        message.chat = MagicMock(spec=Chat)
        message.chat.id = 789012
        message.text = "Hello, AI!"
        message.answer = AsyncMock()
        message.bot = MagicMock(spec=Bot)
        message.bot.send_chat_action = AsyncMock()
        return message

    @pytest.mark.asyncio
    async def test_full_message_flow(
        self, mock_telegram_message: MagicMock, mock_config: AppConfig
    ) -> None:
        """Тест полного цикла обработки сообщения."""
        # Arrange
        mock_user = User(
            id=1,
            telegram_id=123456,
            username="testuser",
            first_name="Test",
            last_name="User",
            daily_message_count=5,
            is_premium=False,
        )

        # Mock session context manager for conversation service
        mock_session_ctx_conv = MagicMock()
        mock_session_conv = AsyncMock()
        mock_session_ctx_conv.__aenter__.return_value = mock_session_conv

        # Create a mock save_conversation function to pass to the handler
        mock_save_conversation = AsyncMock(return_value=True)

        with patch(
            "app.handlers.message.generate_ai_response"
        ) as mock_generate_response:
            mock_generate_response.return_value = (
                "AI response",
                10,
                "test-model",
                0.5,
            )

            # Mock session context managers for conversation service
            with patch(
                "app.handlers.message.get_session",
                return_value=mock_session_ctx_conv,
            ):
                with patch(
                    "app.handlers.message.get_config",
                    return_value=mock_config,
                ):
                    # Act
                    await handle_text_message(
                        mock_telegram_message, mock_user, "ru", mock_save_conversation
                    )

                    # Assert
                    # All components should be called
                    mock_generate_response.assert_called_once()
                    mock_save_conversation.assert_called_once()
                    mock_telegram_message.answer.assert_called_once()


class TestMessageSanitization:
    """Тесты функции санитизации сообщений."""

    def test_sanitize_telegram_message_removes_special_tags(self) -> None:
        """Тест удаления специальных тегов из сообщения."""
        # Arrange
        text_with_tags = "Hello ｜begin▁of▁sentence｜world｜end▁of▁sentence｜!"

        # Act
        sanitized = sanitize_telegram_message(text_with_tags)

        # Assert
        assert sanitized == "Hello world!"

    def test_sanitize_telegram_message_replaces_non_breaking_spaces(self) -> None:
        """Тест замены неразрывных пробелов."""
        # Arrange
        text_with_nbsp = "Hello\u00a0world\u2007test\u202fend"

        # Act
        sanitized = sanitize_telegram_message(text_with_nbsp)

        # Assert
        assert sanitized == "Hello world test end"

    def test_sanitize_telegram_message_truncates_long_messages(self) -> None:
        """Тест обрезки слишком длинных сообщений."""
        # Arrange
        long_text = "A" * 5000

        # Act
        sanitized = sanitize_telegram_message(long_text)

        # Assert
        assert len(sanitized) == 4096
        assert sanitized.endswith("...")

    def test_sanitize_telegram_message_real_world_example(self) -> None:
        """Тест санитизации реального примера с ошибкой Telegram."""
        # Arrange
        # This is based on the actual error we saw in the logs
        ai_response_with_special_tags = "Это пример ответа с ｜begin▁of▁sentence｜специальными тегами｜end▁of▁sentence｜ которые вызывают ошибку в Telegram."

        # Act
        sanitized = sanitize_telegram_message(ai_response_with_special_tags)

        # Assert
        # The special tags should be removed
        assert "｜begin▁of▁sentence｜" not in sanitized
        assert "｜end▁of▁sentence｜" not in sanitized
        # The rest of the text should remain
        assert "Это пример ответа с" in sanitized
        assert "специальными тегами" in sanitized
        assert "которые вызывают ошибку в Telegram." in sanitized
