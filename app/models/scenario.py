"""
@file: models/scenario.py
@description: Модель сценария для ролевых игр
@dependencies: sqlalchemy, datetime
@created: 2025-11-21
"""

from datetime import datetime
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
    from app.models.chat import Chat
    from app.models.user import User


class Scenario(Base):
    """Модель сценария для ролевых игр"""

    __tablename__ = "scenarios"

    # Основные поля
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, comment="Уникальный ID сценария"
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True, comment="Название сценария"
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Описание сценария"
    )
    initial_prompt: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Стартовый промпт сценария"
    )

    # Настройки
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Активен ли сценарий"
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Публичный ли сценарий"
    )
    min_age_rating: Mapped[int] = mapped_column(
        Integer, default=18, nullable=False, comment="Минимальный возрастной рейтинг"
    )

    # Метаинформация
    created_by_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id"),
        nullable=True,
        comment="ID пользователя-создателя",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), comment="Дата создания"
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        comment="Дата последнего обновления",
    )

    # Статистика
    total_chats: Mapped[int] = mapped_column(
        Integer, default=0, comment="Общее количество чатов"
    )
    total_messages: Mapped[int] = mapped_column(
        Integer, default=0, comment="Общее количество сообщений"
    )

    # Связи
    chats: Mapped[list["Chat"]] = relationship("Chat", back_populates="scenario")
    created_by: Mapped["User | None"] = relationship(
        "User", foreign_keys=[created_by_user_id]
    )

    # Индексы
    __table_args__ = (
        Index("idx_scenario_title_active", "title", "is_active"),
        Index("idx_scenario_created_by", "created_by_user_id"),
    )

    def __repr__(self) -> str:
        return f"<Scenario(id={self.id}, title='{self.title}')>"

    @property
    def popularity_score(self) -> int:
        """Индекс популярности сценария"""
        return self.total_chats + self.total_messages


# Экспорт для удобного использования
__all__ = ["Scenario"]
