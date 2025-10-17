"""
@file: user.py
@description: Модель пользователя Telegram бота с поддержкой премиум статуса
@dependencies: sqlalchemy, datetime, pydantic
@created: 2025-09-07
@updated: 2025-10-15
"""

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any

from aiogram.types import Message
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import get_config
from app.database import Base, get_session

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.payment import Payment


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

    # Поля для персонализированной эмоциональной поддержки
    emotional_profile: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Профиль эмоциональных предпочтений пользователя",
    )

    support_preferences: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Предпочтения в типе поддержки",
    )

    communication_style: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Предпочтительный стиль общения",
    )

    # Отношения
    # Use string annotation for forward reference to avoid circular import
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
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

    def __init__(self, **kwargs: Any) -> None:
        # Set default values for fields that don't have database defaults
        if "is_premium" not in kwargs:
            kwargs["is_premium"] = False
        if "is_blocked" not in kwargs:
            kwargs["is_blocked"] = False
        if "is_active" not in kwargs:
            kwargs["is_active"] = True
        if "daily_message_count" not in kwargs:
            kwargs["daily_message_count"] = 0
        if "total_messages" not in kwargs:
            kwargs["total_messages"] = 0

        super().__init__(**kwargs)

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
        # If user is not premium, return False
        if not self.is_premium:
            return False

        # If user is premium but no expiration date, consider it active
        if not self.premium_expires_at:
            return True

        return datetime.now(UTC) <= self.premium_expires_at

    def can_send_message(self, free_limit: int = 10) -> bool:
        """Проверка возможности отправки сообщения."""
        if self.is_blocked:
            return False

        # Сброс счетчика если прошел день
        today = date.today()
        if self.last_message_date is not None and self.last_message_date < today:
            return True

        # Получаем конфигурацию для лимитов
        config = get_config()

        # Для премиум пользователей используем премиум лимит из конфигурации
        if self.is_premium_active():
            premium_limit = getattr(config.user_limits, "premium_message_limit", 100)
            return self.daily_message_count < premium_limit

        # Для обычных пользователей используем переданный лимит
        return self.daily_message_count < free_limit

    def reset_daily_count_if_needed(self) -> bool:
        """Сброс дневного счетчика если прошел день."""
        # Сброс счетчика если прошел день
        today = datetime.now(UTC).date()
        if self.last_message_date is not None and self.last_message_date < today:
            self.daily_message_count = 0
            self.last_message_date = today
            return True
        return False

    def increment_message_count(self) -> None:
        """Увеличение счетчика сообщений пользователя."""
        self.daily_message_count += 1
        self.total_messages = (self.total_messages or 0) + 1
        self.last_message_date = datetime.now(UTC).date()

    def update_emotional_profile(self, profile_data: dict[str, Any]) -> None:
        """Обновление эмоционального профиля пользователя."""
        if self.emotional_profile is None:
            self.emotional_profile = {}
        self.emotional_profile.update(profile_data)

    def update_support_preferences(self, preferences: dict[str, Any]) -> None:
        """Обновление предпочтений в типе поддержки."""
        if self.support_preferences is None:
            self.support_preferences = {}
        self.support_preferences.update(preferences)

    def get_emotional_profile(self) -> dict[str, Any]:
        """Получение эмоционального профиля пользователя."""
        return self.emotional_profile or {}

    def get_support_preferences(self) -> dict[str, Any]:
        """Получение предпочтений в типе поддержки."""
        return self.support_preferences or {}


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
    is_premium: bool | None = None
    is_active: bool | None = None
    is_blocked: bool | None = None
    daily_message_count: int | None = Field(None, ge=0)
    premium_expires_at: datetime | None = None
    last_message_date: date | None = None
    emotional_profile: dict[str, Any] | None = None
    support_preferences: dict[str, Any] | None = None
    communication_style: str | None = Field(None, max_length=50)


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
    emotional_profile: dict[str, Any] | None
    support_preferences: dict[str, Any] | None
    communication_style: str | None

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
