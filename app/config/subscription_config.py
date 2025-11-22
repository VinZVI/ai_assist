"""
@file: config/subscription_config.py
@description: Конфигурация уровней подписок
@dependencies: app.models.subscription
@created: 2025-11-22
"""

from datetime import timedelta
from typing import Dict, Any
from app.models.subscription import SubscriptionTier


class SubscriptionConfig:
    """Конфигурация уровней подписок"""

    TIER_SETTINGS = {
        SubscriptionTier.FREE: {
            "daily_message_limit": 20,
            "daily_image_limit": 0,
            "memory_retention_days": None,  # Только кэш
            "has_image_generation": False,
            "has_priority_queue": False,
            "has_no_ads": False,
            "max_characters_creation": 5,
            "max_scenarios_per_character": 1,
            "response_speed": "minimal",
            "storage": "cache_only",
            "queue_priority": "low",
        },
        SubscriptionTier.STANDARD: {
            "daily_message_limit": 100,
            "daily_image_limit": 0,
            "memory_retention_days": 7,
            "has_image_generation": False,
            "has_priority_queue": True,
            "has_no_ads": True,
            "max_characters_creation": 10,
            "max_scenarios_per_character": 3,
            "response_speed": "maximum",
            "storage": "database",
            "queue_priority": "normal",
        },
        SubscriptionTier.PREMIUM: {
            "daily_message_limit": 300,
            "daily_image_limit": 60,
            "memory_retention_days": 30,
            "has_image_generation": True,
            "has_priority_queue": True,
            "has_no_ads": True,
            "max_characters_creation": None,  # Безлимит
            "max_scenarios_per_character": None,  # Безлимит
            "response_speed": "maximum",
            "storage": "database",
            "queue_priority": "high",
        },
        SubscriptionTier.DELUXE: {
            "daily_message_limit": None,  # Безлимит
            "daily_image_limit": None,  # Безлимит
            "memory_retention_days": None,  # Безлимит
            "has_image_generation": True,
            "has_priority_queue": True,
            "has_no_ads": True,
            "max_characters_creation": None,  # Безлимит
            "max_scenarios_per_character": None,  # Безлимит
            "response_speed": "maximum",
            "storage": "permanent",
            "queue_priority": "highest",
        },
        SubscriptionTier.ADMIN: {
            "daily_message_limit": None,  # Безлимит
            "daily_image_limit": None,  # Безлимит
            "memory_retention_days": None,  # Безлимит
            "has_image_generation": True,
            "has_priority_queue": True,
            "has_no_ads": True,
            "max_characters_creation": None,  # Безлимит
            "max_scenarios_per_character": None,  # Безлимит
            "response_speed": "maximum",
            "storage": "permanent",
            "queue_priority": "admin",
            "admin_features": True,
        },
    }

    # Цены подписок в Telegram Stars
    PRICES = {
        SubscriptionTier.STANDARD: 100,
        SubscriptionTier.PREMIUM: 300,
        SubscriptionTier.DELUXE: 500,
    }

    # Длительность подписок в днях
    DURATION_DAYS = {
        SubscriptionTier.STANDARD: 30,
        SubscriptionTier.PREMIUM: 30,
        SubscriptionTier.DELUXE: 30,
    }

    @classmethod
    def get_tier_settings(cls, tier: SubscriptionTier) -> Dict[str, Any]:
        """Получение настроек уровня подписки"""
        return cls.TIER_SETTINGS.get(tier, cls.TIER_SETTINGS[SubscriptionTier.FREE])

    @classmethod
    def get_tier_price(cls, tier: SubscriptionTier) -> int:
        """Получение цены подписки"""
        return cls.PRICES.get(tier, 0)

    @classmethod
    def get_tier_duration(cls, tier: SubscriptionTier) -> int:
        """Получение длительности подписки в днях"""
        return cls.DURATION_DAYS.get(tier, 30)


# Экспорт для удобного использования
__all__ = ["SubscriptionConfig"]
