"""
@file: models/character.py
@description: Модель персонажа ИИ для ролевых игр
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
    from app.models.character_rating import CharacterRating
    from app.models.character_tag import CharacterTag
    from app.models.chat import Chat
    from app.models.user import User


class Character(Base):
    """Модель персонажа ИИ"""

    __tablename__ = "characters"

    # Основные поля
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="Уникальный ID персонажа"
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Имя персонажа"
    )
    gender: Mapped[str] = mapped_column(
        Enum('male', 'female', 'other', name='character_gender'),
        nullable=False,
        comment="Пол персонажа"
    )
    age: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Возраст персонажа"
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Характер персонажа"
    )

    # Системные поля
    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="URL аватара персонажа"
    )
    system_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Промпт для ИИ"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Активен ли персонаж"
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Публичный ли персонаж"
    )

    # Метаинформация
    created_by_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id"),
        nullable=True,
        comment="ID пользователя-создателя"
    )
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
    total_chats: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Общее количество чатов"
    )
    total_messages: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Общее количество сообщений"
    )
    rating_sum: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Сумма рейтингов"
    )
    rating_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Количество оценок"
    )

    # Связи
    tags: Mapped[list["CharacterTag"]] = relationship(
        "CharacterTag",
        back_populates="character",
        cascade="all, delete-orphan"
    )
    ratings: Mapped[list["CharacterRating"]] = relationship(
        "CharacterRating",
        back_populates="character",
        cascade="all, delete-orphan"
    )
    chats: Mapped[list["Chat"]] = relationship(
        "Chat",
        back_populates="character"
    )
    created_by: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[created_by_user_id]
    )

    # Индексы
    __table_args__ = (
        Index('idx_character_name_active', 'name', 'is_active'),
        Index('idx_character_created_by', 'created_by_user_id'),
    )

    def __repr__(self) -> str:
        return f"<Character(id={self.id}, name='{self.name}')>"

    @property
    def average_rating(self) -> float:
        """Средний рейтинг персонажа"""
        if self.rating_count == 0:
            return 0.0
        return self.rating_sum / self.rating_count

    @property
    def popularity_score(self) -> int:
        """Индекс популярности"""
        return self.total_chats + self.total_messages + (self.rating_sum * 2)


# Экспорт для удобного использования
__all__ = ["Character"]