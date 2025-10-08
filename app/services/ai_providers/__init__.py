"""
@file: ai_providers/__init__.py
@description: Модуль провайдеров AI с поддержкой множественных API
@dependencies: .base, .openrouter
@created: 2025-09-20
"""

from .base import (
    AIProviderError,
    AIResponse,
    APIAuthenticationError,
    APIConnectionError,
    APIQuotaExceededError,
    APIRateLimitError,
    BaseAIProvider,
    ConversationMessage,
)
from .openrouter import OpenRouterProvider

# Экспорт всех классов провайдеров
__all__ = [
    "AIProviderError",
    # Базовые классы
    "AIResponse",
    "APIAuthenticationError",
    "APIConnectionError",
    "APIQuotaExceededError",
    "APIRateLimitError",
    "BaseAIProvider",
    "ConversationMessage",
    # Провайдеры
    "OpenRouterProvider",
]
