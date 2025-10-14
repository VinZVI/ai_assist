"""
@file: services/payment_service.py
@description: Сервис для обработки платежей Telegram Stars
@dependencies: aiogram, sqlalchemy, datetime
@created: 2025-10-10
"""

from datetime import datetime, timedelta
from typing import Optional

from aiogram import Bot
from aiogram.types import LabeledPrice, SuccessfulPayment
from loguru import logger
from sqlalchemy import select, update

from app.config import get_config
from app.database import get_session
from app.lexicon.gettext import get_log_text
from app.models.payment import Payment
from app.models.user import User
from app.services.user_service import get_or_update_user


class TelegramStarsPaymentService:
    """Сервис для обработки платежей Telegram Stars."""

    def __init__(self, bot: Bot) -> None:
        """
        Инициализация сервиса платежей.

        Args:
            bot: Экземпляр бота для отправки инвойсов
        """
        self.bot = bot

    async def create_invoice(
        self, user_id: int, amount: int, description: str, duration_days: int
    ) -> bool:
        """
        Создание инвойса для оплаты Telegram Stars.

        Args:
            user_id: ID пользователя в Telegram
            amount: Сумма в Telegram Stars
            description: Описание платежа
            duration_days: Длительность премиум подписки в днях

        Returns:
            bool: Успешность создания инвойса
        """
        try:
            # Создаем payload с информацией о пользователе и длительности подписки
            payload = f"premium_{user_id}_{duration_days}"

            await self.bot.send_invoice(
                chat_id=user_id,
                title="AI-Companion Premium",
                description=description,
                payload=payload,
                provider_token="",  # Пустой для Telegram Stars
                currency="XTR",  # Telegram Stars
                prices=[LabeledPrice(label="Premium Access", amount=amount)],
                start_parameter="premium_purchase",
            )
            logger.info(
                get_log_text("payment.invoice_created").format(
                    user_id=user_id, amount=amount
                )
            )
            return True
        except Exception as e:
            logger.error(
                get_log_text("payment.invoice_creation_error").format(
                    user_id=user_id, error=str(e)
                )
            )
            return False

    async def handle_successful_payment(
        self, payment: SuccessfulPayment, user_telegram_id: int
    ) -> bool:
        """
        Обработка успешного платежа и активация премиум статуса.

        Args:
            payment: Объект успешного платежа
            user_telegram_id: ID пользователя в Telegram

        Returns:
            bool: Успешность обработки платежа
        """
        try:
            # Парсим payload для получения информации о пользователе и длительности
            payload_parts = payment.invoice_payload.split("_")
            if len(payload_parts) >= 3:
                user_id_from_payload = int(payload_parts[1])
                duration_days = int(payload_parts[2])
            else:
                logger.error(
                    get_log_text("payment.invalid_payload").format(
                        payload=payment.invoice_payload
                    )
                )
                return False

            # Логируем платеж в базе данных
            async with get_session() as session:
                payment_record = Payment(
                    user_id=user_id_from_payload,
                    amount=payment.total_amount,
                    payment_id=payment.telegram_payment_charge_id,
                    payment_provider="telegram_stars",
                    status="completed",
                    created_at=datetime.utcnow(),
                )
                session.add(payment_record)
                await session.commit()

            # Активируем премиум статус
            success = await self.activate_premium(user_id_from_payload, duration_days)
            if success:
                logger.info(
                    get_log_text("payment.payment_processed").format(
                        user_id=user_id_from_payload,
                        amount=payment.total_amount,
                        duration=duration_days,
                    )
                )
            else:
                logger.error(
                    get_log_text("payment.premium_activation_failed").format(
                        user_id=user_id_from_payload
                    )
                )

            return success

        except Exception as e:
            logger.error(
                get_log_text("payment.payment_handling_error").format(
                    user_id=user_telegram_id, error=str(e)
                )
            )
            return False

    async def activate_premium(self, user_id: int, duration_days: int) -> bool:
        """
        Активация премиум статуса для пользователя.

        Args:
            user_id: ID пользователя в системе
            duration_days: Длительность премиум подписки в днях

        Returns:
            bool: Успешность активации премиум статуса
        """
        try:
            async with get_session() as session:
                # Получаем пользователя
                stmt = select(User).where(User.id == user_id)
                result = await session.execute(stmt)
                user = await result.scalar_one_or_none()

                if not user:
                    logger.error(
                        get_log_text("payment.user_not_found").format(user_id=user_id)
                    )
                    return False

                # Рассчитываем новую дату окончания премиум подписки
                current_time = datetime.utcnow()
                if user.premium_expires_at and user.premium_expires_at > current_time:
                    # Продлеваем существующую подписку
                    new_premium_until = user.premium_expires_at + timedelta(
                        days=duration_days
                    )
                else:
                    # Новая активация премиум подписки
                    new_premium_until = current_time + timedelta(days=duration_days)

                # Обновляем пользователя
                update_stmt = (
                    update(User)
                    .where(User.id == user_id)
                    .values(
                        is_premium=True,
                        premium_expires_at=new_premium_until,
                    )
                )
                await session.execute(update_stmt)
                await session.commit()

                logger.info(
                    get_log_text("payment.premium_activated").format(
                        user_id=user_id,
                        expires_at=new_premium_until.isoformat(),
                        duration=duration_days,
                    )
                )
                return True

        except Exception as e:
            logger.error(
                get_log_text("payment.premium_activation_error").format(
                    user_id=user_id, error=str(e)
                )
            )
            return False

    async def deactivate_premium(self, user_id: int) -> bool:
        """
        Деактивация премиум статуса для пользователя.

        Args:
            user_id: ID пользователя в системе

        Returns:
            bool: Успешность деактивации премиум статуса
        """
        try:
            async with get_session() as session:
                update_stmt = (
                    update(User).where(User.id == user_id).values(is_premium=False)
                )
                await session.execute(update_stmt)
                await session.commit()

                logger.info(
                    get_log_text("payment.premium_deactivated").format(user_id=user_id)
                )
                return True

        except Exception as e:
            logger.error(
                get_log_text("payment.premium_deactivation_error").format(
                    user_id=user_id, error=str(e)
                )
            )
            return False

    async def check_premium_status(self, user_id: int) -> dict:
        """
        Проверка статуса премиум подписки пользователя.

        Args:
            user_id: ID пользователя в системе

        Returns:
            dict: Словарь с информацией о статусе премиум подписки
        """
        try:
            async with get_session() as session:
                stmt = select(User).where(User.id == user_id)
                result = await session.execute(stmt)
                user = await result.scalar_one_or_none()

                if not user:
                    return {"is_premium": False, "expires_at": None, "remaining_days": 0}

                current_time = datetime.utcnow()
                is_active = (
                    user.is_premium
                    and user.premium_expires_at
                    and user.premium_expires_at > current_time
                )

                return {
                    "is_premium": is_active,
                    "expires_at": user.premium_expires_at.isoformat()
                    if user.premium_expires_at
                    else None,
                    "remaining_days": (
                        user.premium_expires_at - current_time
                    ).days
                    if is_active and user.premium_expires_at
                    else 0,
                }

        except Exception as e:
            logger.error(
                get_log_text("payment.premium_status_check_error").format(
                    user_id=user_id, error=str(e)
                )
            )
            return {"is_premium": False, "expires_at": None, "remaining_days": 0}


# Экспорт для удобного использования
__all__ = ["TelegramStarsPaymentService"]