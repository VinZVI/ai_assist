"""
@file: models/__init__.py
@description: Модели данных приложения
@dependencies: sqlalchemy, pydantic
@created: 2025-09-07
@updated: 2025-09-12
"""

# Импорт базового класса для моделей
from app.database import Base
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

# Импорт всех моделей
from app.models.payment import Payment
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
    "Conversation",
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
    # Модели SQLAlchemy
    "Payment",
    "User",
    # Pydantic схемы для User
    "UserBase",
    "UserCreate",
    "UserResponse",
    "UserStats",
    "UserUpdate",
]
