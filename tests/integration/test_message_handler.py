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
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import Bot
from aiogram.types import Chat, Message
from aiogram.types import User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.message import (
    create_system_message,
    generate_ai_response,
    get_or_update_user,
    get_recent_conversation_history,
    handle_text_message,
    save_conversation,
)
from app.models import Conversation, User
from app.services import AIResponse, AIServiceError, ConversationMessage


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
    async def test_get_existing_user(
        self, mock_message: MagicMock, mock_session: AsyncSession
    ) -> None:
        """Тест получения существующего пользователя."""
        # Arrange
        existing_user = User(
            telegram_id=12345,
            username="test_user",
            first_name="Test",
            daily_message_count=5,
        )

        mock_session.get.return_value = existing_user

        with patch("app.handlers.message.get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Act
            result = await get_or_update_user(mock_message)

            # Assert
            assert result is not None
            assert result.telegram_id == 12345
            assert result.username == "test_user"
            mock_session.get.assert_called_once_with(User, 12345)
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_not_found(
        self, mock_message: Message, mock_session: AsyncSession
    ) -> None:
        """Тест случая когда пользователь не найден."""
        # Arrange
        mock_session.get.return_value = None

        with patch("app.handlers.message.get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Act
            result = await get_or_update_user(mock_message)

            # Assert
            assert result is None

    @pytest.mark.asyncio
    async def test_message_without_user(self, mock_session: AsyncSession) -> None:
        """Тест обработки сообщения без данных пользователя."""
        # Arrange
        message = MagicMock(spec=Message)
        message.from_user = None

        # Act
        result = await get_or_update_user(message)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_database_error(
        self, mock_message: Message, mock_session: AsyncSession
    ) -> None:
        """Тест обработки ошибки базы данных."""
        # Arrange
        mock_session.get.side_effect = Exception("Database error")

        with patch("app.handlers.message.get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Act
            result = await get_or_update_user(mock_message)

            # Assert
            assert result is None
            mock_session.rollback.assert_called_once()


class TestGetRecentConversationHistory:
    """Тесты функции get_recent_conversation_history."""

    @pytest.mark.asyncio
    async def test_get_conversation_history(self, mock_session: AsyncSession) -> None:
        """Тест получения истории диалогов."""
        # Arrange
        user_id = 12345
        conversations = [
            Conversation(
                telegram_user_id=user_id,
                role="USER",
                content="Hello",
                created_at=datetime(2025, 9, 12, 10, 0),
            ),
            Conversation(
                telegram_user_id=user_id,
                role="ASSISTANT",
                content="Hi there!",
                created_at=datetime(2025, 9, 12, 10, 1),
            ),
        ]

        # Мокаем результат запроса
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = conversations
        mock_session.execute.return_value = mock_result

        # Act
        result = await get_recent_conversation_history(mock_session, user_id, limit=5)

        # Assert
        assert len(result) == 2
        assert result[0].role == "user"
        assert result[0].content == "Hello"
        assert result[1].role == "assistant"
        assert result[1].content == "Hi there!"

    @pytest.mark.asyncio
    async def test_empty_conversation_history(self, mock_session: AsyncSession) -> None:
        """Тест получения пустой истории диалогов."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        # Act
        result = await get_recent_conversation_history(mock_session, 12345, limit=5)

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_conversation_history_database_error(
        self, mock_session: AsyncSession
    ) -> None:
        """Тест обработки ошибки при получении истории."""
        # Arrange
        mock_session.execute.side_effect = Exception("Database error")

        # Act
        result = await get_recent_conversation_history(mock_session, 12345, limit=5)

        # Assert
        assert result == []


class TestSaveConversation:
    """Тесты функции save_conversation."""

    @pytest.mark.asyncio
    async def test_save_conversation_success(self, mock_session: AsyncSession) -> None:
        """Тест успешного сохранения диалога."""
        # Arrange
        user_id = 12345
        user_message = "Hello AI"
        ai_response = "Hello human!"
        ai_model = "deepseek-chat"
        tokens_used = 25
        response_time = 1.5

        # Act
        result = await save_conversation(
            mock_session,
            user_id,
            user_message,
            ai_response,
            ai_model,
            tokens_used,
            response_time,
        )

        # Assert
        assert result is True
        assert mock_session.add.call_count == 2  # User + AI messages
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_conversation_database_error(
        self, mock_session: AsyncSession
    ) -> None:
        """Тест обработки ошибки при сохранении диалога."""
        # Arrange
        mock_session.add.side_effect = Exception("Database error")

        # Act
        result = await save_conversation(
            mock_session,
            12345,
            "test",
            "test",
            "model",
            0,
            0.0,
        )

        # Assert
        assert result is False
        mock_session.rollback.assert_called_once()


class TestCreateSystemMessage:
    """Тесты функции create_system_message."""

    def test_create_system_message(self) -> None:
        """Тест создания системного сообщения."""
        # Act
        message = create_system_message()

        # Assert
        assert isinstance(message, ConversationMessage)
        assert message.role == "system"
        assert "эмпатичный AI-помощник" in message.content
        assert "поддержку и понимание" in message.content


class TestGenerateAiResponse:
    """Тесты функции generate_ai_response."""

    @pytest.fixture
    def mock_user(self) -> User:
        """Создает мок пользователя."""
        return User(
            telegram_id=12345,
            username="test_user",
            first_name="Test",
            daily_message_count=1,
        )

    @pytest.mark.asyncio
    async def test_generate_ai_response_success(
        self, mock_user: User, mock_session: AsyncSession
    ) -> None:
        """Тест успешной генерации AI ответа."""
        # Arrange
        mock_ai_service = MagicMock()
        mock_ai_response = AIResponse(
            content="This is AI response",
            tokens_used=30,
            model="deepseek-chat",
        )
        mock_ai_service.generate_response.return_value = mock_ai_response

        # Мокаем историю диалогов
        with patch(
            "app.handlers.message.get_recent_conversation_history",
        ) as mock_get_history:
            mock_get_history.return_value = []

            with patch("app.handlers.message.get_ai_service") as mock_get_ai:
                mock_get_ai.return_value = mock_ai_service

                with patch("app.handlers.message.get_session") as mock_get_session:
                    mock_get_session.return_value.__aenter__.return_value = mock_session

                    # Act
                    content, tokens, model, time = await generate_ai_response(
                        mock_user,
                        "Hello AI",
                    )

                    # Assert
                    assert content == "This is AI response"
                    assert tokens == 30
                    assert model == "deepseek-chat"
                    assert time > 0

    @pytest.mark.asyncio
    async def test_generate_ai_response_api_error(
        self, mock_user: User, mock_session: AsyncSession
    ) -> None:
        """Тест обработки ошибки AI API."""
        # Arrange
        mock_ai_service = MagicMock()
        mock_ai_service.generate_response.side_effect = AIServiceError("API Error")

        with patch(
            "app.handlers.message.get_recent_conversation_history",
        ) as mock_get_history:
            mock_get_history.return_value = []

            with patch("app.handlers.message.get_ai_service") as mock_get_ai:
                mock_get_ai.return_value = mock_ai_service

                with patch("app.handlers.message.get_session") as mock_get_session:
                    mock_get_session.return_value.__aenter__.return_value = mock_session

                    # Act
                    content, tokens, model, time = await generate_ai_response(
                        mock_user,
                        "Hello AI",
                    )

                    # Assert
                    assert "временные технические трудности" in content
                    assert tokens == 0
                    assert model == "fallback"
                    assert time == 0.0

    @pytest.mark.asyncio
    async def test_generate_ai_response_unexpected_error(
        self, mock_user: User, mock_session: AsyncSession
    ) -> None:
        """Тест обработки неожиданной ошибки."""
        # Arrange
        with patch("app.handlers.message.get_ai_service") as mock_get_ai:
            mock_get_ai.side_effect = Exception("Unexpected error")

            with patch("app.handlers.message.get_session") as mock_get_session:
                mock_get_session.return_value.__aenter__.return_value = mock_session

                # Act
                content, tokens, model, time = await generate_ai_response(
                    mock_user,
                    "Hello AI",
                )

                # Assert
                assert "Произошла неожиданная ошибка" in content
                assert tokens == 0
                assert model == "error"
                assert time == 0.0


class TestHandleTextMessage:
    """Тесты главной функции handle_text_message."""

    @pytest.fixture
    def mock_message(self) -> MagicMock:
        """Создает полный мок сообщения."""
        message = MagicMock(spec=Message)
        message.from_user = MagicMock(spec=TelegramUser)
        message.from_user.id = 12345
        message.text = "Hello AI!"
        message.chat = MagicMock(spec=Chat)
        message.chat.id = 67890
        message.bot = MagicMock(spec=Bot)
        message.answer = AsyncMock()
        message.reply = AsyncMock()
        return message

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        """Создает мок пользователя с активными лимитами."""
        user = MagicMock(spec=User)
        user.user_id = 12345
        user.daily_message_count = 5
        user.can_send_message.return_value = True
        user.reset_daily_count_if_needed.return_value = None
        user.increment_message_count.return_value = None
        return user

    @pytest.mark.asyncio
    async def test_handle_text_message_success(
        self,
        mock_message: Message,
        mock_user: User,
        mock_session: AsyncSession,
    ) -> None:
        """Тест успешной обработки текстового сообщения."""
        # Arrange
        with patch("app.handlers.message.get_or_update_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("app.handlers.message.generate_ai_response") as mock_generate:
                mock_generate.return_value = ("AI response", 25, "deepseek-chat", 1.2)

                with patch("app.handlers.message.get_session") as mock_get_session:
                    mock_get_session.return_value.__aenter__.return_value = mock_session
                    mock_session.get.return_value = mock_user

                    with patch("app.handlers.message.save_conversation") as mock_save:
                        mock_save.return_value = True

                        # Act
                        await handle_text_message(mock_message)

                        # Assert
                        mock_message.answer.assert_called_once_with(
                            text="AI response",
                            parse_mode="Markdown",
                        )
                        mock_user.increment_message_count.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_text_message_no_user_data(self) -> None:
        """Тест обработки сообщения без данных пользователя."""
        # Arrange
        message = MagicMock(spec=Message)
        message.from_user = None
        message.text = "Hello"

        # Act
        await handle_text_message(message)

        # Assert - функция должна завершиться без ошибок

    @pytest.mark.asyncio
    async def test_handle_text_message_no_text(self, mock_message: Message) -> None:
        """Тест обработки сообщения без текста."""
        # Arrange
        mock_message.text = None

        # Act
        await handle_text_message(mock_message)

        # Assert - функция должна завершиться без ошибок

    @pytest.mark.asyncio
    async def test_handle_text_message_too_short(self, mock_message: Message) -> None:
        """Тест обработки слишком короткого сообщения."""
        # Arrange
        mock_message.text = "a"

        # Act
        await handle_text_message(mock_message)

        # Assert
        mock_message.answer.assert_called_once()
        assert (
            "более содержательное сообщение" in mock_message.answer.call_args[1]["text"]
        )

    @pytest.mark.asyncio
    async def test_handle_text_message_too_long(self, mock_message: Message) -> None:
        """Тест обработки слишком длинного сообщения."""
        # Arrange
        mock_message.text = "a" * 2001  # Больше 2000 символов

        # Act
        await handle_text_message(mock_message)

        # Assert
        mock_message.answer.assert_called_once()
        assert "слишком длинное" in mock_message.answer.call_args[1]["text"]

    @pytest.mark.asyncio
    async def test_handle_text_message_unregistered_user(
        self, mock_message: Message
    ) -> None:
        """Тест обработки сообщения от незарегистрированного пользователя."""
        # Arrange
        with patch("app.handlers.message.get_or_update_user") as mock_get_user:
            mock_get_user.return_value = None

            # Act
            await handle_text_message(mock_message)

            # Assert
            mock_message.answer.assert_called_once()
            assert "команды /start" in mock_message.answer.call_args[1]["text"]

    @pytest.mark.asyncio
    async def test_handle_text_message_limit_exceeded(
        self, mock_message: Message, mock_session: AsyncSession
    ) -> None:
        """Тест обработки сообщения при превышении лимита."""
        # Arrange
        mock_user = MagicMock(spec=User)
        mock_user.can_send_message.return_value = False
        mock_user.daily_message_count = 10
        mock_user.reset_daily_count_if_needed.return_value = None

        with patch("app.handlers.message.get_or_update_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("app.handlers.message.get_config") as mock_get_config:
                mock_config = MagicMock()
                mock_config.user_limits.premium_price = 99
                mock_config.user_limits.free_messages_limit = 10
                mock_get_config.return_value = mock_config

                # Act
                await handle_text_message(mock_message)

                # Assert
                mock_message.answer.assert_called_once()
                assert (
                    "Превышен дневной лимит" in mock_message.answer.call_args[1]["text"]
                )

    @pytest.mark.asyncio
    async def test_handle_text_message_critical_error(
        self, mock_message: Message, mock_user: User
    ) -> None:
        """Тест обработки критической ошибки."""
        # Arrange
        with patch("app.handlers.message.get_or_update_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch("app.handlers.message.generate_ai_response") as mock_generate:
                mock_generate.side_effect = Exception("Critical error")

                # Act
                await handle_text_message(mock_message)

                # Assert
                mock_message.answer.assert_called_once()
                assert "Произошла ошибка" in mock_message.answer.call_args[1]["text"]


class TestMessageHandlerIntegration:
    """Интеграционные тесты обработчика сообщений."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_message_flow(
        self, mock_message: Message, mock_user: User, mock_session: AsyncSession
    ) -> None:
        """Тест полного потока обработки сообщения."""
        # Arrange - мокаем все зависимости
        with patch("app.handlers.message.get_or_update_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            with patch(
                "app.handlers.message.get_recent_conversation_history",
            ) as mock_get_history:
                mock_get_history.return_value = []

                mock_ai_service = MagicMock()
                mock_ai_response = AIResponse(
                    content="Понимаю ваши чувства. Как дела?",
                    tokens_used=15,
                    model="deepseek-chat",
                )
                mock_ai_service.generate_response.return_value = mock_ai_response

                with patch("app.handlers.message.get_ai_service") as mock_get_ai:
                    mock_get_ai.return_value = mock_ai_service

                    with patch("app.handlers.message.get_session") as mock_get_session:
                        mock_get_session.return_value.__aenter__.return_value = (
                            mock_session
                        )
                        mock_session.get.return_value = mock_user

                        with patch(
                            "app.handlers.message.save_conversation",
                        ) as mock_save:
                            mock_save.return_value = True

                            # Act
                            await handle_text_message(mock_message)

                            # Assert
                            # Проверяем что все этапы выполнены
                            mock_get_user.assert_called_once()
                            mock_user.reset_daily_count_if_needed.assert_called_once()
                            mock_user.can_send_message.assert_called_once()
                            mock_ai_service.generate_response.assert_called_once()
                            mock_user.increment_message_count.assert_called_once()
                            mock_save.assert_called_once()
                            mock_message.answer.assert_called_once()

                            # Проверяем содержимое ответа
                            assert (
                                mock_message.answer.call_args[1]["text"]
                                == "Понимаю ваши чувства. Как дела?"
                            )
                            assert (
                                mock_message.answer.call_args[1]["parse_mode"]
                                == "Markdown"
                            )


# Маркеры для pytest
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.handlers,
    pytest.mark.message_handler,
]
