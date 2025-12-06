"""
@file: services/subscription_service.py
@description: Сервис управления подписками
@dependencies: sqlalchemy, app.models.subscription, app.subscription_config.subscription_config
@created: 2025-11-22
"""

from datetime import UTC, date, datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import AppConfig
from app.models.subscription import (
    Subscription,
    SubscriptionStatus,
    SubscriptionTier,
    SubscriptionUsage,
)
from app.subscription_config import SubscriptionConfig


class SubscriptionService:
    """Сервис управления подписками"""

    def __init__(self, db_session: AsyncSession, config: AppConfig):
        self.db = db_session
        self.config = config

    async def get_user_subscription(self, user_id: int) -> Subscription:
        """Получение подписки пользователя"""
        result = await self.db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            # Создаем бесплатную подписку по умолчанию
            subscription = await self.create_free_subscription(user_id)

        return subscription

    async def create_free_subscription(self, user_id: int) -> Subscription:
        """Создание бесплатной подписки"""
        settings = SubscriptionConfig.get_tier_settings(SubscriptionTier.FREE)

        subscription = Subscription(
            user_id=user_id,
            tier=SubscriptionTier.FREE,
            status=SubscriptionStatus.ACTIVE,
            daily_message_limit=settings["daily_message_limit"],
            daily_image_limit=settings["daily_image_limit"],
            memory_retention_days=settings["memory_retention_days"],
            has_image_generation=settings["has_image_generation"],
            has_priority_queue=settings["has_priority_queue"],
            has_no_ads=settings["has_no_ads"],
            max_characters_creation=settings["max_characters_creation"],
            max_scenarios_per_character=settings["max_scenarios_per_character"],
            started_at=datetime.now(UTC),
        )

        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)

        return subscription

    async def upgrade_subscription(
        self,
        user_id: int,
        new_tier: SubscriptionTier,
        payment_data: dict[str, Any] | None = None,
    ) -> Subscription:
        """Обновление подписки до нового уровня"""
        subscription = await self.get_user_subscription(user_id)
        settings = SubscriptionConfig.get_tier_settings(new_tier)
        duration_days = SubscriptionConfig.get_tier_duration(new_tier)

        # Обновляем параметры подписки
        subscription.tier = new_tier
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.daily_message_limit = settings["daily_message_limit"]
        subscription.daily_image_limit = settings["daily_image_limit"]
        subscription.memory_retention_days = settings["memory_retention_days"]
        subscription.has_image_generation = settings["has_image_generation"]
        subscription.has_priority_queue = settings["has_priority_queue"]
        subscription.has_no_ads = settings["has_no_ads"]
        subscription.max_characters_creation = settings["max_characters_creation"]
        subscription.max_scenarios_per_character = settings[
            "max_scenarios_per_character"
        ]

        # Устанавливаем срок действия
        if new_tier != SubscriptionTier.FREE and new_tier != SubscriptionTier.ADMIN:
            subscription.expires_at = datetime.now(UTC) + timedelta(days=duration_days)
            subscription.last_payment_at = datetime.now(UTC)
            subscription.next_billing_at = subscription.expires_at
        else:
            subscription.expires_at = None
            subscription.last_payment_at = None
            subscription.next_billing_at = None

        # Сохраняем платежную информацию
        if payment_data:
            subscription.payment_provider = payment_data.get("provider")
            subscription.external_subscription_id = payment_data.get("external_id")

        await self.db.commit()
        await self.db.refresh(subscription)

        return subscription

    async def check_usage_limit(
        self,
        user_id: int,
        limit_type: str,  # 'messages', 'images', 'characters', 'scenarios'
        increment: int = 1,
    ) -> bool:
        """Проверка и обновление лимитов использования"""
        subscription = await self.get_user_subscription(user_id)

        # Получаем текущее использование
        today = date.today()
        usage = await self.get_or_create_daily_usage(subscription.id, today)

        # Проверяем лимиты
        if limit_type == "messages":
            current = usage.messages_sent
            limit = subscription.daily_message_limit
            if limit and current + increment > limit:
                return False
            usage.messages_sent += increment

        elif limit_type == "images":
            current = usage.images_generated
            limit = subscription.daily_image_limit
            if limit and current + increment > limit:
                return False
            usage.images_generated += increment

        elif limit_type == "characters":
            current = usage.characters_created
            limit = subscription.max_characters_creation
            if limit and current + increment > limit:
                return False
            usage.characters_created += increment

        elif limit_type == "scenarios":
            current = usage.scenarios_created
            limit = subscription.max_scenarios_per_character
            if limit and current + increment > limit:
                return False
            usage.scenarios_created += increment

        await self.db.commit()
        return True

    async def get_usage_stats(self, user_id: int) -> dict[str, Any]:
        """Получение статистики использования"""
        subscription = await self.get_user_subscription(user_id)
        today = date.today()
        usage = await self.get_or_create_daily_usage(subscription.id, today)

        return {
            "tier": subscription.tier.value,
            "messages": {
                "used": usage.messages_sent,
                "limit": subscription.daily_message_limit,
                "unlimited": subscription.daily_message_limit is None,
            },
            "images": {
                "used": usage.images_generated,
                "limit": subscription.daily_image_limit,
                "unlimited": subscription.daily_image_limit is None,
            },
            "expires_at": subscription.expires_at,
            "days_remaining": subscription.days_until_expiry,
        }

    async def get_or_create_daily_usage(
        self, subscription_id: int, usage_date: date
    ) -> SubscriptionUsage:
        """Получение или создание записи использования за день"""
        result = await self.db.execute(
            select(SubscriptionUsage).where(
                SubscriptionUsage.subscription_id == subscription_id,
                SubscriptionUsage.usage_date == usage_date,
            )
        )
        usage = result.scalar_one_or_none()

        if not usage:
            usage = SubscriptionUsage(
                subscription_id=subscription_id, usage_date=usage_date
            )
            self.db.add(usage)
            await self.db.commit()
            await self.db.refresh(usage)

        return usage

    async def is_user_premium(self, user_id: int) -> bool:
        """Проверка, является ли пользователь премиум-пользователем"""
        subscription = await self.get_user_subscription(user_id)
        return subscription.tier in {
            SubscriptionTier.STANDARD,
            SubscriptionTier.PREMIUM,
            SubscriptionTier.DELUXE,
            SubscriptionTier.ADMIN,
        }

    async def has_feature_access(self, user_id: int, feature: str) -> bool:
        """Проверка доступа к определенной функции"""
        subscription = await self.get_user_subscription(user_id)
        settings = SubscriptionConfig.get_tier_settings(subscription.tier)

        if feature == "image_generation":
            return settings["has_image_generation"]
        if feature == "priority_queue":
            return settings["has_priority_queue"]
        if feature == "no_ads":
            return settings["has_no_ads"]
        if feature == "admin_features":
            return settings.get("admin_features", False)

        return False

    async def get_user_tier(self, user_id: int) -> SubscriptionTier:
        """Получение уровня подписки пользователя"""
        subscription = await self.get_user_subscription(user_id)
        return subscription.tier

    async def cancel_subscription(self, user_id: int) -> bool:
        """Отмена подписки"""
        subscription = await self.get_user_subscription(user_id)
        if subscription.tier in {SubscriptionTier.FREE, SubscriptionTier.ADMIN}:
            return False

        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = datetime.now(UTC)
        await self.db.commit()
        return True

    async def extend_subscription(self, user_id: int, days: int) -> bool:
        """Продление подписки на указанное количество дней"""
        subscription = await self.get_user_subscription(user_id)
        if subscription.tier in {SubscriptionTier.FREE, SubscriptionTier.ADMIN}:
            return False

        subscription.expires_at = datetime.now(UTC) + timedelta(days=days)
        subscription.next_billing_at = subscription.expires_at
        await self.db.commit()
        return True


# Экспорт для удобного использования
__all__ = ["SubscriptionService"]
