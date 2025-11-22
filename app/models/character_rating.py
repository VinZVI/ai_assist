"""
@file: models/character_rating.py
@description: Модель рейтингов персонажей от пользователей
@dependencies: sqlalchemy, datetime
@created: 2025-11-21
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.character import Character
    from app.models.user import User


class CharacterRating(Base):
    """Рейтинги персонажей от пользователей"""

    __tablename__ = "character_ratings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Уникальный ID рейтинга"
    )
    character_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("characters.id"),
        nullable=False,
        comment="ID персонажа"
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id"),
        nullable=False,
        comment="ID пользователя"
    )
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Рейтинг (1 = дизлайк, 5 = лайк)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        comment="Дата создания"
    )

    # Связи
    character: Mapped["Character"] = relationship(
        "Character",
        back_populates="ratings"
    )
    user: Mapped["User"] = relationship("User")

    # Ограничения
    __table_args__ = (
        UniqueConstraint('character_id', 'user_id', name='uq_character_user_rating'),
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        Index('idx_character_rating', 'character_id'),
        Index('idx_user_rating', 'user_id'),
    )

    def __repr__(self) -> str:
        return f"<CharacterRating(id={self.id}, character_id={self.character_id}, user_id={self.user_id}, rating={self.rating})>"


# Экспорт для удобного использования
__all__ = ["CharacterRating"]