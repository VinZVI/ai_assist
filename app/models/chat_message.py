"""
@file: models/chat_message.py
@description: Модель сообщения в чате
@dependencies: sqlalchemy, datetime
@created: 2025-11-21
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.chat import Chat


class ChatMessage(Base):
    """Модель сообщения в чате"""

    __tablename__ = "chat_messages"

    # Основные поля
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, comment="Уникальный ID сообщения"
    )
    chat_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chats.id"), nullable=False, index=True, comment="ID чата"
    )

    # Содержимое сообщения
    message_type: Mapped[str] = mapped_column(
        Enum("user", "ai", "system", name="message_type"),
        nullable=False,
        index=True,
        comment="Тип сообщения",
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Содержимое сообщения"
    )
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, comment="Дополнительные данные"
    )

    # Для ИИ сообщений
    ai_model: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Модель ИИ"
    )
    generation_time_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Время генерации в миллисекундах"
    )
    token_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Количество токенов"
    )

    # Системные поля
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), index=True, comment="Дата создания"
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Удалено ли сообщение"
    )

    # Связи
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")

    # Индексы для производительности
    __table_args__ = (
        Index("idx_chat_created", "chat_id", "created_at"),
        Index("idx_chat_type_created", "chat_id", "message_type", "created_at"),
        Index("idx_message_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, chat_id={self.chat_id}, type='{self.message_type}')>"


# Экспорт для удобного использования
__all__ = ["ChatMessage"]
