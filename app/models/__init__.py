"""
@file: models/__init__.py
@description: Модели данных приложения
@dependencies: sqlalchemy, pydantic
@created: 2025-09-07
@updated: 2025-09-12
"""

# Импорт базового класса для моделей
from app.database import Base

# Импорт всех SQLAlchemy моделей (важно для разрешения relationships)
from app.models.character import Character
from app.models.character_rating import CharacterRating
from app.models.character_tag import CharacterTag
from app.models.chat import Chat
from app.models.chat_message import ChatMessage
from app.models.conversation import (
    Conversation,
    ConversationBase,
    ConversationCreate,
    ConversationHistory,
    ConversationResponse,
    ConversationStats,
    ConversationStatus,
    ConversationUpdate,
    MessageRole,
)
from app.models.payment import Payment
from app.models.scenario import Scenario
from app.models.subscription import Subscription, SubscriptionUsage, SubscriptionStatus
from app.models.user import (
    User,
    UserBase,
    UserCreate,
    UserResponse,
    UserStats,
    UserUpdate,
)

# Экспорт всех моделей и схем
__all__ = [
    # База данных
    "Base",
    # SQLAlchemy модели (важно импортировать все для разрешения relationships)
    "Character",
    "CharacterRating",
    "CharacterTag",
    "Chat",
    "ChatMessage",
    "Conversation",
    "Payment",
    "Scenario",
    "Subscription",
    "SubscriptionUsage",
    "SubscriptionStatus",
    "User",
    # Pydantic схемы для Conversation
    "ConversationBase",
    "ConversationCreate",
    "ConversationHistory",
    "ConversationResponse",
    "ConversationStats",
    "ConversationStatus",
    "ConversationUpdate",
    # Enums
    "MessageRole",
    # Pydantic схемы для User
    "UserBase",
    "UserCreate",
    "UserResponse",
    "UserStats",
    "UserUpdate",
]
