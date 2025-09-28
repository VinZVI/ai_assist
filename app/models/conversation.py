"""
@file: conversation.py
@description: Модель диалога пользователя с AI
@dependencies: sqlalchemy, datetime
@created: 2025-09-07
"""

from datetime import UTC, datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class MessageRole(str, Enum):
    """Роли сообщений в диалоге."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(str, Enum):
    """Статусы обработки сообщения."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Conversation(Base):
    """Модель для хранения истории диалогов с ИИ."""

    __tablename__ = "conversations"

    # Основные поля
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Уникальный ID сообщения",
    )

    # Связь с пользователем
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID пользователя",
    )

    # Содержимое сообщения
    message_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Текст сообщения пользователя",
    )

    response_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Ответ ИИ на сообщение",
    )

    # Роль сообщения
    role: Mapped[MessageRole] = mapped_column(
        String(20),
        nullable=False,
        default=MessageRole.USER,
        comment="Роль отправителя сообщения",
    )

    # Статус обработки
    status: Mapped[ConversationStatus] = mapped_column(
        String(20),
        nullable=False,
        default=ConversationStatus.PENDING,
        index=True,
        comment="Статус обработки сообщения",
    )

    # Метаданные Telegram
    message_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="ID сообщения в Telegram",
    )

    chat_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="ID чата в Telegram",
    )

    # Метаданные ИИ
    ai_model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default="deepseek-chat",
        comment="Модель ИИ, использованная для ответа",
    )

    tokens_used: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Количество токенов, использованных в запросе",
    )

    response_time_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Время ответа ИИ в миллисекундах",
    )

    # Дополнительные метаданные в JSON
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Дополнительные метаданные в JSON формате",
    )

    # Ошибки
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Сообщение об ошибке если статус FAILED",
    )

    error_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Код ошибки",
    )

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        comment="Время создания сообщения",
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время обработки ИИ",
    )

    # Отношения
    # Use string annotation for forward reference to avoid circular import
    user: Mapped["User"] = relationship(
        "User",
        back_populates="conversations",
        lazy="select",
    )

    # Индексы
    __table_args__ = (
        Index("idx_conv_user_created", "user_id", "created_at"),
        Index("idx_conv_status", "status"),
        Index("idx_conv_created", "created_at"),
        Index("idx_conv_user_status", "user_id", "status"),
        Index("idx_conv_telegram", "chat_id", "message_id"),
        # Ограничения
        CheckConstraint("tokens_used >= 0", name="check_tokens_positive"),
        CheckConstraint("response_time_ms >= 0", name="check_response_time_positive"),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="check_status_valid",
        ),
        CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name="check_role_valid",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Conversation(id={self.id}, user_id={self.user_id}, "
            f"status='{self.status}')>"
        )

    def is_completed(self) -> bool:
        """Проверка завершенности обработки сообщения."""
        return self.status == ConversationStatus.COMPLETED

    def is_failed(self) -> bool:
        """Проверка наличия ошибки в обработке."""
        return self.status == ConversationStatus.FAILED

    def get_processing_time(self) -> int | None:
        """Получение времени обработки в миллисекундах."""
        if self.processed_at and self.created_at:
            delta = self.processed_at - self.created_at
            return int(delta.total_seconds() * 1000)
        return None

    def mark_as_processing(self) -> None:
        """Отметить сообщение как обрабатываемое."""
        self.status = ConversationStatus.PROCESSING

    def mark_as_completed(self, response: str, tokens: int | None = None) -> None:
        """Отметить сообщение как завершенное."""
        self.status = ConversationStatus.COMPLETED
        self.response_text = response
        self.processed_at = datetime.now(UTC)
        if tokens:
            self.tokens_used = tokens

    def mark_as_failed(self, error_msg: str, error_code: str | None = None) -> None:
        """Отметить сообщение как проваленное."""
        self.status = ConversationStatus.FAILED
        self.error_message = error_msg
        self.error_code = error_code
        self.processed_at = datetime.now(UTC)


# Pydantic схемы для валидации и сериализации


class ConversationBase(BaseModel):
    """Базовая схема диалога."""

    message_text: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Текст сообщения",
    )
    role: MessageRole = Field(default=MessageRole.USER, description="Роль отправителя")
    message_id: int | None = Field(None, description="ID сообщения в Telegram")
    chat_id: int | None = Field(None, description="ID чата в Telegram")

    @field_validator("message_text")
    @classmethod
    def validate_message_text(cls, v: str) -> str:
        """Валидация текста сообщения."""
        v = v.strip()
        if not v:
            msg = "Текст сообщения не может быть пустым"
            raise ValueError(msg)
        return v


class ConversationCreate(ConversationBase):
    """Схема для создания диалога."""

    user_id: int = Field(..., gt=0, description="ID пользователя")


class ConversationUpdate(BaseModel):
    """Схема для обновления диалога."""

    response_text: str | None = Field(None, max_length=8000)
    status: ConversationStatus | None = None
    ai_model: str | None = Field(None, max_length=100)
    tokens_used: int | None = Field(None, ge=0)
    response_time_ms: int | None = Field(None, ge=0)
    error_message: str | None = None
    error_code: str | None = Field(None, max_length=50)
    metadata: dict[str, Any] | None = None


class ConversationResponse(ConversationBase):
    """Схема для возврата данных диалога."""

    id: int
    user_id: int
    response_text: str | None
    status: ConversationStatus
    ai_model: str | None
    tokens_used: int | None
    response_time_ms: int | None
    error_message: str | None
    created_at: datetime
    processed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ConversationStats(BaseModel):
    """Схема для статистики диалогов."""

    total_conversations: int
    completed_conversations: int
    failed_conversations: int
    avg_response_time_ms: float | None
    total_tokens_used: int | None
    conversations_today: int

    model_config = ConfigDict(from_attributes=True)


class ConversationHistory(BaseModel):
    """Схема для истории диалогов пользователя."""

    conversations: list[ConversationResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool

    model_config = ConfigDict(from_attributes=True)


# Экспорт для удобного использования
__all__ = [
    "Conversation",
    "ConversationBase",
    "ConversationCreate",
    "ConversationHistory",
    "ConversationResponse",
    "ConversationStats",
    "ConversationStatus",
    "ConversationUpdate",
    "MessageRole",
]
