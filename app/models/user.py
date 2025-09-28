"""
@file: user.py
@description: Модель пользователя для базы данных
@dependencies: sqlalchemy, datetime
@created: 2025-09-07
"""

from datetime import UTC, date, datetime, timezone
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class User(Base):
    """Модель пользователя Telegram бота."""

    __tablename__ = "users"

    # Основные поля
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Внутренний ID пользователя",
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
        comment="ID пользователя в Telegram",
    )

    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Username пользователя в Telegram",
    )

    first_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Имя пользователя",
    )

    last_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Фамилия пользователя",
    )

    language_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        default="ru",
        comment="Код языка пользователя",
    )

    # Премиум статус
    is_premium: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Статус премиум пользователя",
    )

    premium_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата окончания премиум подписки",
    )

    # Лимиты сообщений
    daily_message_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Количество сообщений за сегодня",
    )

    last_message_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=func.current_date(),
        comment="Дата последнего сообщения",
    )

    total_messages: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Общее количество сообщений",
    )

    # Статус пользователя
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Активен ли пользователь",
    )

    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Заблокирован ли пользователь",
    )

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        comment="Дата регистрации",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        comment="Дата последнего обновления",
    )

    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время последней активности",
    )

    # Отношения
    # Use string annotation for forward reference to avoid circular import
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Индексы
    __table_args__ = (
        Index("idx_user_telegram_id", "telegram_id"),
        Index("idx_user_premium", "is_premium"),
        Index("idx_user_active", "is_active"),
        Index("idx_user_created", "created_at"),
        Index("idx_user_last_message", "last_message_date"),
        # Ограничения
        CheckConstraint(
            "daily_message_count >= 0",
            name="check_daily_message_count_positive",
        ),
        CheckConstraint("total_messages >= 0", name="check_total_messages_positive"),
        CheckConstraint("telegram_id > 0", name="check_telegram_id_positive"),
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, telegram_id={self.telegram_id}, "
            f"username='{self.username}')>"
        )

    def get_display_name(self) -> str:
        """Получение отображаемого имени пользователя."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        if self.username:
            return f"@{self.username}"
        return f"User {self.telegram_id}"

    def is_premium_active(self) -> bool:
        """Проверка активности премиум статуса."""
        if not self.premium_expires_at:
            return False

        return datetime.now(UTC) <= self.premium_expires_at

    def can_send_message(self, free_limit: int = 10) -> bool:
        """Проверка возможности отправки сообщения."""
        if self.is_blocked:
            return False

        if self.is_premium_active():
            return True

        # Сброс счетчика если прошел день
        today = date.today()
        if self.last_message_date < today:
            return True

        return self.daily_message_count < free_limit

    def reset_daily_count_if_needed(self) -> bool:
        """Сброс дневного счетчика если прошел день."""
        # Сброс счетчика если прошел день
        today = datetime.now(UTC).date()
        if self.last_message_date < today:
            return True
        return False


# Pydantic схемы для валидации и сериализации


class UserBase(BaseModel):
    """Базовая схема пользователя."""

    telegram_id: int = Field(..., gt=0, description="ID пользователя в Telegram")
    username: str | None = Field(
        None,
        max_length=255,
        description="Username в Telegram",
    )
    first_name: str | None = Field(None, max_length=255, description="Имя пользователя")
    last_name: str | None = Field(
        None,
        max_length=255,
        description="Фамилия пользователя",
    )
    language_code: str | None = Field("ru", max_length=10, description="Код языка")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str | None) -> str | None:
        """Валидация username."""
        if v is not None and v.strip() == "":
            return None
        return v


class UserCreate(UserBase):
    """Схема для создания пользователя."""


class UserUpdate(BaseModel):
    """Схема для обновления пользователя."""

    username: str | None = Field(None, max_length=255)
    first_name: str | None = Field(None, max_length=255)
    last_name: str | None = Field(None, max_length=255)
    language_code: str | None = Field(None, max_length=10)
    is_active: bool | None = None
    is_blocked: bool | None = None


class UserResponse(UserBase):
    """Схема для возврата данных пользователя."""

    id: int
    is_premium: bool
    daily_message_count: int
    total_messages: int
    is_active: bool
    is_blocked: bool
    created_at: datetime
    last_activity_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserStats(BaseModel):
    """Схема для статистики пользователя."""

    total_users: int
    active_users: int
    premium_users: int
    new_users_today: int
    messages_today: int

    model_config = ConfigDict(from_attributes=True)


# Экспорт для удобного использования
__all__ = [
    "User",
    "UserBase",
    "UserCreate",
    "UserResponse",
    "UserStats",
    "UserUpdate",
]

# Add this at the end of the file to resolve the forward reference
