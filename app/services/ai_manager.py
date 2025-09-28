"""
@file: ai_manager.py
@description: Менеджер AI провайдеров с поддержкой fallback
@dependencies: pydantic, loguru, app.config, app.services.ai_providers
@created: 2025-09-12
"""

from datetime import UTC, datetime, timedelta, timezone
from typing import ClassVar

from loguru import logger

from app.config import get_config
from app.services.ai_providers import DeepSeekProvider, OpenRouterProvider
from app.services.ai_providers.base import (
    AIProviderError,
    AIResponse,
    APIAuthenticationError,
    APIConnectionError,
    APIQuotaExceededError,
    APIRateLimitError,
    BaseAIProvider,
)


class AIManager:
    _providers: ClassVar[list[BaseAIProvider]] = [
        OpenRouterProvider(),
        DeepSeekProvider(),
    ]
    _cache: dict[str, dict[str, AIResponse | datetime]] = {}
    _ttl: int = 60

    def __init__(self) -> None:
        self._config = get_config()

    def fetch(self, provider: str, key: str) -> AIResponse:
        if key in self._cache:
            entry = self._cache[key]
            if datetime.now(UTC) - entry["timestamp"] < timedelta(seconds=self._ttl):
                logger.debug(
                    f"🎯 Найден кешированный ответ для {provider}: {key[:8]}...",
                )
                return entry["response"]

        for p in self._providers:
            if p.name == provider:
                try:
                    response = p.fetch(key)
                    self._cache[key] = {
                        "response": response,
                        "timestamp": datetime.now(UTC),
                    }
                    logger.debug(f"💾 Ответ {provider} сохранен в кеш: {key[:8]}...")
                    return response
                except (
                    APIAuthenticationError,
                    APIConnectionError,
                    APIQuotaExceededError,
                    APIRateLimitError,
                ) as e:
                    logger.error(
                        f"💡 Ошибка при запросе к {provider}: {e}",
                    )
                    raise AIProviderError from e

        raise AIProviderError(f"Неизвестный провайдер: {provider}")
