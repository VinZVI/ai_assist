"""
@file: models/character_tag.py
@description: Модель тегов для персонажей
@dependencies: sqlalchemy
@created: 2025-11-21
"""

from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.character import Character


class CharacterTag(Base):
    """Теги для персонажей"""

    __tablename__ = "character_tags"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Уникальный ID тега"
    )
    character_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("characters.id"),
        nullable=False,
        comment="ID персонажа"
    )
    tag_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Название тега"
    )

    # Связи
    character: Mapped["Character"] = relationship(
        "Character",
        back_populates="tags"
    )

    # Ограничения
    __table_args__ = (
        UniqueConstraint('character_id', 'tag_name', name='uq_character_tag'),
        Index('idx_tag_name', 'tag_name'),
        Index('idx_character_tag', 'character_id'),
    )

    def __repr__(self) -> str:
        return f"<CharacterTag(id={self.id}, character_id={self.character_id}, tag='{self.tag_name}')>"


# Экспорт для удобного использования
__all__ = ["CharacterTag"]