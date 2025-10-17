"""
@file: models/payment.py
@description: Модель платежей Telegram Stars для премиум подписки
@dependencies: sqlalchemy, datetime
@created: 2025-10-10
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Payment(Base):
    """Модель для хранения информации о платежах Telegram Stars."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Внутренний ID платежа",
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="ID пользователя в системе",
    )

    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Сумма платежа в Telegram Stars",
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="XTR",
        comment="Валюта платежа (XTR для Telegram Stars)",
    )

    payment_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Провайдер платежа (telegram_stars)",
    )

    payment_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="ID платежа от Telegram",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="completed",
        comment="Статус платежа (completed, refunded, failed)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        comment="Дата и время создания записи",
    )

    # Отношения
    user: Mapped["User"] = relationship("User", back_populates="payments")

    # Индексы
    __table_args__ = (
        Index("idx_payments_user_id", "user_id"),
        Index("idx_payments_created_at", "created_at"),
        Index("idx_payments_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Payment(id={self.id}, user_id={self.user_id}, "
            f"amount={self.amount}, status='{self.status}')>"
        )


# Экспорт для удобного использования
__all__ = ["Payment"]
