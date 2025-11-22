"""
@file: models/chat.py
@description: Модель чата между пользователем и персонажем в рамках сценария
@dependencies: sqlalchemy, datetime
@created: 2025-11-21
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.character import Character
    from app.models.chat_message import ChatMessage
    from app.models.scenario import Scenario
    from app.models.user import User


class Chat(Base):
    """Модель чата между пользователем и персонажем в рамках сценария"""

    __tablename__ = "chats"

    # Основные поля
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="Уникальный ID чата"
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id"),
        nullable=False,
        index=True,
        comment="ID пользователя"
    )
    character_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("characters.id"),
        nullable=False,
        index=True,
        comment="ID персонажа"
    )
    scenario_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("scenarios.id"),
        nullable=True,
        index=True,
        comment="ID сценария"
    )

    # Настройки чата
    title: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Пользовательское название"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Активен ли чат"
    )

    # Управление памятью
    memory_retention_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Дней хранения памяти (null = безлимит)"
    )
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время последнего сообщения"
    )

    # Метаинформация
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        comment="Дата создания"
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        comment="Дата последнего обновления"
    )

    # Статистика
    total_messages: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Общее количество сообщений"
    )
    user_messages_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Количество сообщений пользователя"
    )
    ai_messages_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Количество сообщений ИИ"
    )

    # Связи
    user: Mapped["User"] = relationship(
        "User",
        back_populates="chats"
    )
    character: Mapped["Character"] = relationship(
        "Character",
        back_populates="chats"
    )
    scenario: Mapped["Scenario | None"] = relationship(
        "Scenario",
        back_populates="chats"
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="chat",
        cascade="all, delete-orphan"
    )

    # Индексы
    __table_args__ = (
        Index('idx_user_character_scenario', 'user_id', 'character_id', 'scenario_id'),
        Index('idx_user_active_chats', 'user_id', 'is_active'),
        Index('idx_last_message', 'last_message_at'),
        Index('idx_chat_created_at', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<Chat(id={self.id}, user_id={self.user_id}, character_id={self.character_id})>"

    @property
    def should_expire(self) -> bool:
        """Проверка необходимости удаления по сроку хранения"""
        if not self.memory_retention_days or not self.last_message_at:
            return False

        expiry_date = self.last_message_at + timedelta(days=self.memory_retention_days)
        return datetime.utcnow() > expiry_date


# Экспорт для удобного использования
__all__ = ["Chat"]