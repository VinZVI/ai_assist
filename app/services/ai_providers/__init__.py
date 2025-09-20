"""  
@file: ai_providers/__init__.py
@description: Модуль провайдеров AI с поддержкой множественных API
@dependencies: .base, .deepseek, .openrouter
@created: 2025-09-20
"""

from .base import (
    AIResponse,
    ConversationMessage,
    AIProviderError,
    APIConnectionError,
    APIRateLimitError,
    APIAuthenticationError,
    APIQuotaExceededError,
    BaseAIProvider,
)
from .deepseek import DeepSeekProvider
from .openrouter import OpenRouterProvider

# Экспорт всех классов провайдеров
__all__ = [
    # Базовые классы
    "AIResponse",
    "ConversationMessage",
    "AIProviderError",
    "APIConnectionError",
    "APIRateLimitError",
    "APIAuthenticationError",
    "APIQuotaExceededError",
    "BaseAIProvider",
    # Провайдеры
    "DeepSeekProvider",
    "OpenRouterProvider",
]