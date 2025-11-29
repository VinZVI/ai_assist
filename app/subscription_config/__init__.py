"""
@file: subscription_config/__init__.py
@description: Subscription configuration package initialization
@dependencies: app.subscription_config.subscription_config
@created: 2025-11-22
"""

# Import configuration modules
from .subscription_config import SubscriptionConfig, SubscriptionTier

# Export for convenient usage
__all__ = [
    "SubscriptionConfig",
    "SubscriptionTier",
]
