"""
@file: test_models.py
@description: Тесты для моделей данных User и Conversation
@dependencies: pytest, pytest-asyncio, sqlalchemy
@created: 2025-09-12
"""

import pytest
from datetime import datetime, date, timedelta
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserCreate, UserUpdate, UserResponse
from app.models.conversation import Conversation, ConversationCreate, ConversationUpdate, ConversationResponse, MessageRole
from app.database import get_session, Base, get_engine


@pytest.mark.unit
class TestUserModel:
    """Тесты для модели User."""
    
    @pytest.fixture
    def test_user_data(self):
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
            "last_message_date": date.today()
        }
    
    def test_user_creation(self, test_user_data):
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
        assert user.last_message_date == date.today()
    
    def test_user_defaults(self):
        """Тест значений по умолчанию для User."""
        user = User(telegram_id=999999999)
        
        assert user.username is None
        assert user.first_name is None
        assert user.last_name is None
        assert user.language_code is None  # По умолчанию None в модели
        assert user.is_premium is False
        assert user.premium_expires_at is None
        assert user.daily_message_count == 0
        # last_message_date устанавливается БД через func.current_date()
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        assert user.last_activity_at is None
    
    def test_user_display_name_method(self):
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
    

    
    def test_is_premium_active_method(self):
        """Тест метода is_premium_active."""
        # Пользователь без премиума
        user1 = User(telegram_id=1, is_premium=False)
        assert user1.is_premium_active() is False
        
        # Пользователь с активным премиумом
        user2 = User(
            telegram_id=2, 
            is_premium=True, 
            premium_expires_at=datetime.now() + timedelta(days=10)
        )
        assert user2.is_premium_active() is True
        
        # Пользователь с истекшим премиумом
        user3 = User(
            telegram_id=3, 
            is_premium=True, 
            premium_expires_at=datetime.now() - timedelta(days=1)
        )
        assert user3.is_premium_active() is False
        
        # Пользователь с премиумом без срока окончания
        user4 = User(telegram_id=4, is_premium=True, premium_expires_at=None)
        assert user4.is_premium_active() is True
    
    def test_can_send_message_method(self):
        """Тест метода can_send_message."""
        # Премиум пользователь
        premium_user = User(
            telegram_id=1, 
            is_premium=True, 
            daily_message_count=100,
            last_message_date=date.today()
        )
        assert premium_user.can_send_message() is True
        
        # Обычный пользователь в пределах лимита
        regular_user = User(
            telegram_id=2, 
            is_premium=False, 
            daily_message_count=5,
            last_message_date=date.today()
        )
        assert regular_user.can_send_message() is True
        
        # Обычный пользователь превысил лимит
        limited_user = User(
            telegram_id=3, 
            is_premium=False, 
            daily_message_count=20,
            last_message_date=date.today()
        )
        assert limited_user.can_send_message() is False
    
    def test_reset_daily_count_if_needed_method(self):
        """Тест метода reset_daily_count_if_needed."""
        # Пользователь с сегодняшней датой
        user1 = User(
            telegram_id=1, 
            daily_message_count=5, 
            last_message_date=date.today()
        )
        result1 = user1.reset_daily_count_if_needed()
        assert result1 is False  # Не сброшен
        assert user1.daily_message_count == 5
        
        # Пользователь со вчерашней датой
        user2 = User(
            telegram_id=2, 
            daily_message_count=10, 
            last_message_date=date.today() - timedelta(days=1)
        )
        result2 = user2.reset_daily_count_if_needed()
        assert result2 is True  # Сброшен
        assert user2.daily_message_count == 0
        assert user2.last_message_date == date.today()
    



@pytest.mark.unit
class TestUserPydanticSchemas:
    """Тесты для Pydantic схем User."""
    
    def test_user_create_schema(self):
        """Тест схемы UserCreate."""
        data = {
            "telegram_id": 123456789,
            "username": "testuser",
            "first_name": "Test",
            "language_code": "en"
        }
        
        user_create = UserCreate(**data)
        
        assert user_create.telegram_id == 123456789
        assert user_create.username == "testuser"
        assert user_create.first_name == "Test"
        assert user_create.language_code == "en"
    
    def test_user_create_minimal(self):
        """Тест минимальной схемы UserCreate."""
        user_create = UserCreate(telegram_id=999999999)
        
        assert user_create.telegram_id == 999999999
        assert user_create.username is None
        assert user_create.first_name is None
        assert user_create.language_code == "ru"  # Значение по умолчанию
    
    def test_user_update_schema(self):
        """Тест схемы UserUpdate."""
        data = {
            "username": "newusername",
            "first_name": "NewName",
            "is_active": True
        }
        
        user_update = UserUpdate(**data)
        
        assert user_update.username == "newusername"
        assert user_update.first_name == "NewName"
        assert user_update.is_active is True
        assert user_update.last_name is None  # Не указано
    
    def test_user_response_schema(self):
        """Тест схемы UserResponse."""
        # Создаем User объект
        user = User(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            is_premium=True,
            daily_message_count=5
        )
        
        # Преобразуем в response схему
        user_response = UserResponse.model_validate(user)
        
        assert user_response.telegram_id == 123456789
        assert user_response.username == "testuser"
        assert user_response.first_name == "Test"
        assert user_response.is_premium is True
        assert user_response.daily_message_count == 5


@pytest.mark.unit
class TestConversationModel:
    """Тесты для модели Conversation."""
    
    @pytest.fixture
    def test_conversation_data(self):
        """Фикстура с тестовыми данными диалога."""
        return {
            "user_id": 1,  # Foreign key to users.id
            "message_text": "Привет, как дела?",
            "role": MessageRole.USER,
            "ai_model": None,
            "tokens_used": 0,
            "response_time_ms": 0
        }
    
    def test_conversation_creation(self, test_conversation_data):
        """Тест создания диалога."""
        conversation = Conversation(**test_conversation_data)
        
        assert conversation.user_id == 1
        assert conversation.role == MessageRole.USER
        assert conversation.message_text == "Привет, как дела?"
        assert conversation.ai_model is None
        assert conversation.tokens_used == 0
        assert conversation.response_time_ms == 0
        assert isinstance(conversation.created_at, datetime)
    
    def test_conversation_with_ai_response(self):
        """Тест создания диалога с ответом AI."""
        conversation = Conversation(
            user_id=1,
            role=MessageRole.ASSISTANT,
            message_text="Привет!",
            response_text="Привет! У меня всё отлично, спасибо!",
            ai_model="deepseek-chat",
            tokens_used=25,
            response_time_ms=1500
        )
        
        assert conversation.role == MessageRole.ASSISTANT
        assert conversation.ai_model == "deepseek-chat"
        assert conversation.tokens_used == 25
        assert conversation.response_time_ms == 1500
    
    def test_conversation_role_enum(self):
        """Тест enum для ролей сообщений."""
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.SYSTEM == "system"
        
        # Тест создания с разными ролями
        user_msg = Conversation(user_id=1, role=MessageRole.USER, message_text="Test")
        assistant_msg = Conversation(user_id=1, role=MessageRole.ASSISTANT, message_text="Response")
        system_msg = Conversation(user_id=1, role=MessageRole.SYSTEM, message_text="System")
        
        assert user_msg.role == MessageRole.USER
        assert assistant_msg.role == MessageRole.ASSISTANT
        assert system_msg.role == MessageRole.SYSTEM
    
    def test_conversation_content_validation(self):
        """Тест валидации содержимого сообщения."""
        # Нормальное сообщение
        conversation1 = Conversation(
            user_id=1, 
            role=MessageRole.USER, 
            message_text="Это нормальное сообщение"
        )
        assert len(conversation1.message_text) > 0
        
        # Очень длинное сообщение (должно пройти, ограничения в БД)
        long_content = "А" * 5000
        conversation2 = Conversation(
            user_id=1, 
            role=MessageRole.USER, 
            message_text=long_content
        )
        assert len(conversation2.message_text) == 5000


@pytest.mark.unit
class TestConversationPydanticSchemas:
    """Тесты для Pydantic схем Conversation."""
    
    def test_conversation_create_schema(self):
        """Тест схемы ConversationCreate."""
        data = {
            "user_id": 1,
            "message_text": "Тестовое сообщение",
            "role": MessageRole.USER,
            "message_id": 123,
            "chat_id": 456
        }
        
        conv_create = ConversationCreate(**data)
        
        assert conv_create.user_id == 1
        assert conv_create.role == MessageRole.USER
        assert conv_create.message_text == "Тестовое сообщение"
        assert conv_create.message_id == 123
        assert conv_create.chat_id == 456
    
    def test_conversation_create_minimal(self):
        """Тест минимальной схемы ConversationCreate."""
        conv_create = ConversationCreate(
            user_id=1,
            message_text="Минимальное сообщение"
        )
        
        assert conv_create.user_id == 1
        assert conv_create.role == MessageRole.USER  # По умолчанию
        assert conv_create.message_text == "Минимальное сообщение"
        assert conv_create.message_id is None
        assert conv_create.chat_id is None
    
    def test_conversation_update_schema(self):
        """Тест схемы ConversationUpdate."""
        data = {
            "response_text": "Обновленный ответ",
            "ai_model": "updated-model",
            "tokens_used": 50,
            "status": ConversationStatus.COMPLETED
        }
        
        conv_update = ConversationUpdate(**data)
        
        assert conv_update.response_text == "Обновленный ответ"
        assert conv_update.ai_model == "updated-model"
        assert conv_update.tokens_used == 50
        assert conv_update.status == ConversationStatus.COMPLETED
        assert conv_update.response_time is None  # Не указано
    
    async def test_conversation_response_schema(self):
        """Тест схемы ConversationResponse."""
        # Создаем Conversation объект
        conversation = Conversation(
            user_id=123456789,
            role=MessageRole.ASSISTANT,
            content="Ответ ассистента",
            model_used="deepseek-chat",
            tokens_used=30,
            response_time=2.1
        )
        
        # Преобразуем в response схему
        conv_response = ConversationResponse.model_validate(conversation)
        
        assert conv_response.user_id == 123456789
        assert conv_response.role == MessageRole.ASSISTANT
        assert conv_response.content == "Ответ ассистента"
        assert conv_response.model_used == "deepseek-chat"
        assert conv_response.tokens_used == 30
        assert conv_response.response_time == 2.1


@pytest.mark.asyncio
class TestModelRelationships:
    """Тесты для связей между моделями."""
    
    async def test_user_conversations_relationship(self):
        """Тест связи User -> Conversations."""
        # Этот тест требует реальной БД, поэтому делаем базовую проверку
        user = User(user_id=123456789, username="testuser")
        
        # Проверяем, что атрибут conversations существует
        assert hasattr(user, 'conversations')
        
        # В реальной БД здесь будут связанные conversations
        # assert len(user.conversations) >= 0


@pytest.mark.integration
@pytest.mark.asyncio  
class TestDatabaseIntegration:
    """Интеграционные тесты с базой данных."""
    
    @pytest.fixture
    async def db_session(self):
        """Фикстура для сессии БД."""
        async with get_session() as session:
            yield session
    
    @pytest.mark.skip(reason="Требует настроенную БД")
    async def test_user_crud_operations(self, db_session):
        """Интеграционный тест CRUD операций для User."""
        # CREATE
        user_data = UserCreate(
            user_id=999999999,
            username="testuser_integration",
            first_name="Integration",
            last_name="Test"
        )
        
        user = User(**user_data.model_dump())
        db_session.add(user)
        await db_session.commit()
        
        # READ
        retrieved_user = await db_session.get(User, 999999999)
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser_integration"
        
        # UPDATE
        retrieved_user.first_name = "Updated"
        await db_session.commit()
        
        updated_user = await db_session.get(User, 999999999)
        assert updated_user.first_name == "Updated"
        
        # DELETE
        await db_session.delete(updated_user)
        await db_session.commit()
        
        deleted_user = await db_session.get(User, 999999999)
        assert deleted_user is None
    
    @pytest.mark.skip(reason="Требует настроенную БД")
    async def test_conversation_crud_operations(self, db_session):
        """Интеграционный тест CRUD операций для Conversation."""
        # Сначала создаем пользователя
        user = User(user_id=888888888, username="conv_test_user")
        db_session.add(user)
        await db_session.commit()
        
        try:
            # CREATE conversation
            conv_data = ConversationCreate(
                user_id=888888888,
                role=MessageRole.USER,
                content="Тестовое сообщение для интеграции"
            )
            
            conversation = Conversation(**conv_data.model_dump())
            db_session.add(conversation)
            await db_session.commit()
            
            # READ
            assert conversation.id is not None
            retrieved_conv = await db_session.get(Conversation, conversation.id)
            assert retrieved_conv is not None
            assert retrieved_conv.content == "Тестовое сообщение для интеграции"
            
            # UPDATE
            retrieved_conv.content = "Обновленное сообщение"
            await db_session.commit()
            
            updated_conv = await db_session.get(Conversation, conversation.id)
            assert updated_conv.content == "Обновленное сообщение"
            
        finally:
            # Очистка: удаляем пользователя (conversations удалятся каскадно)
            await db_session.delete(user)
            await db_session.commit()