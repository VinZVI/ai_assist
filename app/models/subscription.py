"""
@file: models/subscription.py
@description: Модели подписки пользователя
@dependencies: sqlalchemy, datetime, enum
@created: 2025-11-22
"""

from datetime import UTC, date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.subscription_config import SubscriptionTier

if TYPE_CHECKING:
    from app.models.user import User


class SubscriptionStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"


class Subscription(Base):
    """Расширенная модель подписки"""

    __tablename__ = "subscriptions"

    # Основные поля
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, comment="Уникальный ID подписки"
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id"),
        nullable=False,
        unique=True,
        comment="ID пользователя",
    )

    # Информация о подписке
    tier: Mapped[SubscriptionTier] = mapped_column(
        SQLEnum(SubscriptionTier),
        default=SubscriptionTier.FREE,
        nullable=False,
        index=True,
        comment="Уровень подписки",
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus),
        default=SubscriptionStatus.ACTIVE,
        nullable=False,
        comment="Статус подписки",
    )

    # Временные рамки
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), comment="Дата начала подписки"
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Дата окончания подписки"
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Дата отмены подписки"
    )

    # Лимиты (кэшируются для производительности)
    daily_message_limit: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Дневной лимит сообщений"
    )
    daily_image_limit: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Дневной лимит изображений"
    )
    memory_retention_days: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Дней хранения памяти (null = безлимит)"
    )

    # Дополнительные возможности
    has_image_generation: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Есть ли возможность генерации изображений",
    )
    has_priority_queue: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Есть ли приоритет в очереди"
    )
    has_no_ads: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Нет ли рекламы"
    )
    max_characters_creation: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Максимум созданных персонажей (null = безлимит)",
    )
    max_scenarios_per_character: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Максимум сценариев на персонажа (null = безлимит)",
    )

    # Платежная информация
    payment_provider: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Провайдер платежа"
    )
    external_subscription_id: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Внешний ID подписки"
    )
    last_payment_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Дата последнего платежа"
    )
    next_billing_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Дата следующего платежа"
    )

    # Метаинформация
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), comment="Дата создания"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        comment="Дата последнего обновления",
    )

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="subscription")
    usage_records: Mapped[list["SubscriptionUsage"]] = relationship(
        "SubscriptionUsage", back_populates="subscription", cascade="all, delete-orphan"
    )

    # Индексы
    __table_args__ = (
        Index("idx_subscription_user_id", "user_id"),
        Index("idx_subscription_tier", "tier"),
        Index("idx_subscription_status", "status"),
        Index("idx_subscription_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user_id={self.user_id}, tier='{self.tier.value}')>"

    @property
    def is_active(self) -> bool:
        """Проверка активности подписки"""
        if self.status != SubscriptionStatus.ACTIVE:
            return False
        if self.expires_at and datetime.now(UTC) > self.expires_at:
            return False
        return True

    @property
    def days_until_expiry(self) -> int:
        """Дней до окончания подписки"""
        if not self.expires_at:
            return -1  # Безлимитная
        delta = self.expires_at - datetime.now(UTC)
        return max(0, delta.days)


class SubscriptionUsage(Base):
    """Отслеживание использования лимитов подписки"""

    __tablename__ = "subscription_usage"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment="Уникальный ID записи использования"
    )
    subscription_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subscriptions.id"), nullable=False, comment="ID подписки"
    )

    # Дата для группировки
    usage_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="Дата использования"
    )

    # Счетчики использования
    messages_sent: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Отправлено сообщений"
    )
    images_generated: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Сгенерировано изображений"
    )
    characters_created: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Создано персонажей"
    )
    scenarios_created: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Создано сценариев"
    )

    # Метаинформация
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), comment="Дата создания"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        comment="Дата последнего обновления",
    )

    # Связи
    subscription: Mapped["Subscription"] = relationship(
        "Subscription", back_populates="usage_records"
    )

    # Ограничения
    __table_args__ = (
        UniqueConstraint(
            "subscription_id", "usage_date", name="uq_subscription_daily_usage"
        ),
        Index("idx_usage_date", "usage_date"),
        Index("idx_subscription_usage", "subscription_id"),
    )

    def __repr__(self) -> str:
        return f"<SubscriptionUsage(id={self.id}, subscription_id={self.subscription_id}, date={self.usage_date})>"


# Экспорт для удобного использования
__all__ = [
    "Subscription",
    "SubscriptionStatus",
    "SubscriptionTier",
    "SubscriptionUsage",
]
