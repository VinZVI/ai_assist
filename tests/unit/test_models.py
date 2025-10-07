"""
@file: test_models.py
@description: Тесты для моделей данных User и Conversation
@dependencies: pytest, pytest-asyncio, sqlalchemy
@created: 2025-09-12
"""

from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.conversation import (
    Conversation,
    ConversationCreate,
    ConversationResponse,
    ConversationStatus,
    ConversationUpdate,
    MessageRole,
)
from app.models.user import User, UserCreate, UserResponse, UserUpdate


@pytest.mark.unit
class TestUserModel:
    """Тесты для модели User."""

    @pytest.fixture
    def test_user_data(self) -> dict[str, Any]:
        """Фикстура с тестовыми данными пользователя."""
        return {
            "telegram_id": 123456789,
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "language_code": "ru",
            "is_premium": False,
            "premium_expires_at": None,
            "daily_message_count": 0,
            "last_message_date": datetime.now(UTC).date(),
        }

    def test_user_creation(self, test_user_data: dict[str, Any]) -> None:
        """Тест создания пользователя."""
        user = User(**test_user_data)

        assert user.telegram_id == 123456789
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.language_code == "ru"
        assert user.is_premium is False
        assert user.premium_expires_at is None
        assert user.daily_message_count == 0
        assert user.last_message_date == datetime.now(UTC).date()

    def test_user_defaults(self) -> None:
        """Тест значений по умолчанию для User."""
        user = User(telegram_id=999999999)

        assert user.username is None
        assert user.first_name is None
        assert user.last_name is None
        assert user.language_code is None  # По умолчанию None в модели
        assert user.is_premium is False
        assert user.premium_expires_at is None
        assert user.daily_message_count == 0
        # When creating objects directly (not through DB), datetime fields are None
        # last_message_date устанавливается БД через func.current_date()
        assert user.created_at is None  # Not set when creating directly
        assert user.updated_at is None  # Not set when creating directly
        assert user.last_activity_at is None

    def test_user_display_name_method(self) -> None:
        """Тест метода get_display_name."""
        # Пользователь с именем и фамилией
        user1 = User(telegram_id=1, first_name="John", last_name="Doe")
        assert user1.get_display_name() == "John Doe"

        # Пользователь только с именем
        user2 = User(telegram_id=2, first_name="Jane")
        assert user2.get_display_name() == "Jane"

        # Пользователь с username
        user3 = User(telegram_id=3, username="cooluser")
        assert user3.get_display_name() == "@cooluser"

        # Пользователь без имени
        user4 = User(telegram_id=4)
        assert user4.get_display_name() == "User 4"

    def test_is_premium_active_method(self) -> None:
        """Тест метода is_premium_active."""
        # Пользователь без премиума
        user1 = User(telegram_id=1, is_premium=False)
        assert user1.is_premium_active() is False

        # Пользователь с активным премиумом
        user2 = User(
            telegram_id=2,
            is_premium=True,
            premium_expires_at=datetime.now(UTC) + timedelta(days=10),
        )
        assert user2.is_premium_active() is True

        # Пользователь с истекшим премиумом
        user3 = User(
            telegram_id=3,
            is_premium=True,
            premium_expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        assert user3.is_premium_active() is False

        # Пользователь с премиумом без срока окончания
        user4 = User(telegram_id=4, is_premium=True, premium_expires_at=None)
        assert user4.is_premium_active() is True

    def test_can_send_message_method(self) -> None:
        """Тест метода can_send_message."""
        # Use a fixed date for consistent testing
        fixed_date = date(2025, 10, 7)

        # Премиум пользователь
        premium_user = User(
            telegram_id=1,
            is_premium=True,
            daily_message_count=100,
            last_message_date=fixed_date,
        )
        assert premium_user.can_send_message() is True

        # Обычный пользователь в пределах лимита
        regular_user = User(
            telegram_id=2,
            is_premium=False,
            daily_message_count=5,
            last_message_date=fixed_date,
        )
        assert regular_user.can_send_message() is True

        # Обычный пользователь превысил лимит
        limited_user = User(
            telegram_id=3,
            is_premium=False,
            daily_message_count=20,
            last_message_date=fixed_date,
        )
        assert limited_user.can_send_message() is False

    def test_reset_daily_count_if_needed_method(self) -> None:
        """Тест метода reset_daily_count_if_needed."""
        # Пользователь с сегодняшней датой
        user1 = User(
            telegram_id=1,
            daily_message_count=5,
            last_message_date=datetime.now(UTC).date(),
        )
        result1 = user1.reset_daily_count_if_needed()
        assert result1 is False  # Не сброшен
        assert user1.daily_message_count == 5

        # Пользователь со вчерашней датой
        user2 = User(
            telegram_id=2,
            daily_message_count=10,
            last_message_date=datetime.now(UTC).date() - timedelta(days=1),
        )
        result2 = user2.reset_daily_count_if_needed()
        assert result2 is True  # Сброшен
        assert user2.daily_message_count == 0
        assert user2.last_message_date == datetime.now(UTC).date()


@pytest.mark.unit
class TestUserPydanticSchemas:
    """Тесты для Pydantic схем User."""

    def test_user_create_schema(self) -> None:
        """Тест схемы UserCreate."""
        data = {
            "telegram_id": 123456789,
            "username": "testuser",
            "first_name": "Test",
            "language_code": "en",
        }

        user_create = UserCreate(**data)

        assert user_create.telegram_id == 123456789
        assert user_create.username == "testuser"
        assert user_create.first_name == "Test"
        assert user_create.language_code == "en"

    def test_user_create_minimal(self) -> None:
        """Тест минимальной схемы UserCreate."""
        user_create = UserCreate(telegram_id=999999999)

        assert user_create.telegram_id == 999999999
        assert user_create.username is None
        assert user_create.first_name is None
        assert user_create.language_code == "ru"  # Значение по умолчанию

    def test_user_update_schema(self) -> None:
        """Тест схемы UserUpdate."""
        data = {
            "first_name": "Updated",
            "last_name": "User",
            "is_premium": True,
            "daily_message_count": 5,
        }

        user_update = UserUpdate(**data)

        assert user_update.first_name == "Updated"
        assert user_update.last_name == "User"
        assert user_update.is_premium is True
        assert user_update.daily_message_count == 5
        assert user_update.username is None  # Не указано
        assert user_update.language_code is None  # Не указано
        assert user_update.premium_expires_at is None  # Не указано
        assert user_update.last_message_date is None  # Не указано

    def test_user_response_schema(self) -> None:
        """Тест схемы UserResponse."""
        # Создаем User объект with all required fields
        from datetime import datetime, timezone

        user = User(
            id=1,
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User",
            language_code="en",
            is_premium=True,
            daily_message_count=5,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # Преобразуем в response схему
        user_response = UserResponse.model_validate(user)

        assert user_response.telegram_id == 123456789
        assert user_response.username == "testuser"
        assert user_response.first_name == "Test"
        assert user_response.last_name == "User"
        assert user_response.language_code == "en"
        assert user_response.is_premium is True
        assert user_response.daily_message_count == 5
        assert isinstance(user_response.created_at, datetime)
        # updated_at is not in the UserResponse schema


@pytest.mark.unit
class TestConversationModel:
    """Тесты для модели Conversation."""

    @pytest.fixture
    def test_conversation_data(self) -> dict[str, Any]:
        """Фикстура с тестовыми данными диалога."""
        return {
            "user_id": 1,
            "message_text": "Тестовое сообщение",
            "response_text": "Тестовый ответ",
            "role": MessageRole.USER,
            "status": ConversationStatus.PENDING,
            "message_id": 123,
            "chat_id": 456,
            "ai_model": "deepseek-chat",
            "tokens_used": 10,
            "response_time_ms": 1500,
            "extra_data": {"test": "data"},
        }

    def test_conversation_creation(
        self, test_conversation_data: dict[str, Any]
    ) -> None:
        """Тест создания диалога."""
        conversation = Conversation(**test_conversation_data)

        assert conversation.user_id == 1
        assert conversation.message_text == "Тестовое сообщение"
        assert conversation.response_text == "Тестовый ответ"
        assert conversation.role == MessageRole.USER
        assert conversation.status == ConversationStatus.PENDING
        assert conversation.message_id == 123
        assert conversation.chat_id == 456
        assert conversation.ai_model == "deepseek-chat"
        assert conversation.tokens_used == 10
        assert conversation.response_time_ms == 1500
        assert conversation.extra_data == {"test": "data"}
        # When creating objects directly (not through DB), datetime fields are None
        # assert isinstance(conversation.created_at, datetime)
        # assert isinstance(conversation.processed_at, type(None))  # Не установлено

    def test_conversation_with_ai_response(self) -> None:
        """Тест создания диалога с ответом AI."""
        conversation = Conversation(
            user_id=1,
            message_text="Привет, как дела?",
            response_text="Привет! У меня всё хорошо, спасибо за вопрос!",
            role=MessageRole.USER,
            status=ConversationStatus.COMPLETED,
            ai_model="deepseek-chat",
            tokens_used=25,
            response_time_ms=1500,
        )

        assert conversation.user_id == 1
        assert conversation.message_text == "Привет, как дела?"
        assert conversation.response_text == (
            "Привет! У меня всё хорошо, спасибо за вопрос!"
        )
        assert conversation.role == MessageRole.USER
        assert conversation.status == ConversationStatus.COMPLETED
        assert conversation.ai_model == "deepseek-chat"
        assert conversation.tokens_used == 25
        assert conversation.response_time_ms == 1500
        # When creating objects directly (not through DB), datetime fields are None
        # assert isinstance(conversation.created_at, datetime)
        # assert isinstance(conversation.processed_at, datetime)

    def test_conversation_role_enum(self) -> None:
        """Тест enum для ролей сообщений."""
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.SYSTEM == "system"

        # Проверяем, что это строки
        assert isinstance(MessageRole.USER, str)
        assert isinstance(MessageRole.ASSISTANT, str)
        assert isinstance(MessageRole.SYSTEM, str)

        # Тест создания с разными ролями
        user_msg = Conversation(user_id=1, role=MessageRole.USER, message_text="Test")
        assistant_msg = Conversation(
            user_id=1,
            role=MessageRole.ASSISTANT,
            message_text="Response",
        )
        system_msg = Conversation(
            user_id=1,
            role=MessageRole.SYSTEM,
            message_text="System",
        )

        assert user_msg.role == MessageRole.USER
        assert assistant_msg.role == MessageRole.ASSISTANT
        assert system_msg.role == MessageRole.SYSTEM

    def test_conversation_content_validation(self) -> None:
        """Тест валидации содержимого сообщения."""
        # Нормальное сообщение
        normal_msg = Conversation(
            user_id=1,
            message_text="Нормальное сообщение",
            role=MessageRole.USER,
        )
        assert normal_msg.message_text == "Нормальное сообщение"

        # Сообщение с системной ролью
        system_msg = Conversation(
            user_id=1,
            message_text="Системное сообщение",
            role=MessageRole.SYSTEM,
        )
        assert system_msg.role == MessageRole.SYSTEM


@pytest.mark.unit
class TestConversationPydanticSchemas:
    """Тесты для Pydantic схем Conversation."""

    def test_conversation_create_schema(self) -> None:
        """Тест схемы ConversationCreate."""
        data = {
            "user_id": 1,
            "message_text": "Тестовое сообщение",
            "role": MessageRole.USER,
            "message_id": 123,
            "chat_id": 456,
        }

        conv_create = ConversationCreate(**data)

        assert conv_create.user_id == 1
        assert conv_create.role == MessageRole.USER
        assert conv_create.message_text == "Тестовое сообщение"
        assert conv_create.message_id == 123
        assert conv_create.chat_id == 456

    def test_conversation_create_minimal(self) -> None:
        """Тест минимальной схемы ConversationCreate."""
        conv_create = ConversationCreate(
            user_id=1,
            message_text="Минимальное сообщение",
        )

        assert conv_create.user_id == 1
        assert conv_create.role == MessageRole.USER  # По умолчанию
        assert conv_create.message_text == "Минимальное сообщение"
        assert conv_create.message_id is None
        assert conv_create.chat_id is None

    def test_conversation_update_schema(self) -> None:
        """Тест схемы ConversationUpdate."""
        data = {
            "response_text": "Обновленный ответ",
            "ai_model": "updated-model",
            "tokens_used": 50,
            "status": ConversationStatus.COMPLETED,
        }

        conv_update = ConversationUpdate(**data)

        assert conv_update.response_text == "Обновленный ответ"
        assert conv_update.ai_model == "updated-model"
        assert conv_update.tokens_used == 50
        assert conv_update.status == ConversationStatus.COMPLETED
        assert conv_update.response_time_ms is None  # Не указано

    def test_conversation_response_schema(self) -> None:
        """Тест схемы ConversationResponse."""
        # Создаем Conversation объект
        from datetime import datetime, timezone

        conversation = Conversation(
            id=1,
            user_id=123456789,
            role=MessageRole.ASSISTANT,
            message_text="Test message",
            response_text="Assistant response",
            status=ConversationStatus.COMPLETED,
            ai_model="deepseek-chat",
            tokens_used=30,
            response_time_ms=2100,
            created_at=datetime.now(UTC),
            processed_at=datetime.now(UTC),
        )

        # Преобразуем в response схему
        conv_response = ConversationResponse.model_validate(conversation)

        assert conv_response.user_id == 123456789
        assert conv_response.role == MessageRole.ASSISTANT
        assert conv_response.message_text == "Test message"
        assert conv_response.response_text == "Assistant response"
        assert conv_response.status == ConversationStatus.COMPLETED
        assert conv_response.ai_model == "deepseek-chat"
        assert conv_response.tokens_used == 30
        assert conv_response.response_time_ms == 2100
        assert isinstance(conv_response.created_at, datetime)
        assert isinstance(conv_response.processed_at, datetime)


@pytest.mark.asyncio
class TestModelRelationships:
    """Тесты для связей между моделями."""

    async def test_user_conversations_relationship(self) -> None:
        """Тест связи User -> Conversations."""
        # Этот тест требует реальной БД, поэтому делаем базовую проверку
        user = User(telegram_id=123456789)

        # Проверяем, что атрибут conversations существует
        assert hasattr(user, "conversations")

        # В реальной БД здесь будут связанные conversations


@pytest.mark.integration
@pytest.mark.asyncio
class TestDatabaseIntegration:
    """Интеграционные тесты с базой данных."""

    @pytest.fixture
    async def db_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Фикстура для сессии БД."""
        async with get_session() as session:
            yield session

    @pytest.mark.skip(reason="Требует настроенную БД")
    async def test_user_crud_operations(self, db_session: AsyncSession) -> None:
        """Интеграционный тест CRUD операций для User."""
        # CREATE
        user = User(
            telegram_id=999999999,
            username="testuser_integration",
            first_name="Test",
            is_premium=False,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        try:
            # READ
            retrieved_user = await db_session.get(User, 999999999)
            assert retrieved_user is not None
            assert retrieved_user.username == "testuser_integration"

            # UPDATE
            retrieved_user.first_name = "Updated"
            await db_session.commit()
            await db_session.refresh(retrieved_user)
            updated_user = await db_session.get(User, 999999999)
            assert updated_user.first_name == "Updated"

            # DELETE
            await db_session.delete(retrieved_user)
            await db_session.commit()
            deleted_user = await db_session.get(User, 999999999)
            assert deleted_user is None

        finally:
            # Cleanup in case of test failure
            user_to_delete = await db_session.get(User, 999999999)
            if user_to_delete:
                await db_session.delete(user_to_delete)
                await db_session.commit()

    @pytest.mark.skip(reason="Требует настроенную БД")
    async def test_conversation_crud_operations(self, db_session: AsyncSession) -> None:
        """Интеграционный тест CRUD операций для Conversation."""
        # Сначала создаем пользователя
        user = User(telegram_id=999999998, username="testuser_conv", first_name="Test")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        try:
            # CREATE
            conversation = Conversation(
                user_id=user.user_id,
                content="Тестовое сообщение для интеграции",
                response="Тестовый ответ для интеграции",
            )
            db_session.add(conversation)
            await db_session.commit()
            await db_session.refresh(conversation)

            # READ
            assert conversation.id is not None
            retrieved_conv = await db_session.get(Conversation, conversation.id)
            assert retrieved_conv is not None
            assert retrieved_conv.content == "Тестовое сообщение для интеграции"

            # UPDATE
            retrieved_conv.content = "Обновленное сообщение"
            await db_session.commit()
            await db_session.refresh(retrieved_conv)
            updated_conv = await db_session.get(Conversation, conversation.id)
            assert updated_conv.content == "Обновленное сообщение"

            # DELETE
            await db_session.delete(retrieved_conv)
            await db_session.commit()
            deleted_conv = await db_session.get(Conversation, conversation.id)
            assert deleted_conv is None

        finally:
            # Cleanup in case of test failure
            conv_to_delete = (
                await db_session.get(Conversation, conversation.id)
                if "conversation" in locals() and conversation.id
                else None
            )
            if conv_to_delete:
                await db_session.delete(conv_to_delete)
            user_to_delete = await db_session.get(User, 999999998)
            if user_to_delete:
                await db_session.delete(user_to_delete)
            if "conv_to_delete" in locals() or "user_to_delete" in locals():
                await db_session.commit()
