"""
@file: ai_providers/base.py
@description: Базовый абстрактный класс для всех AI провайдеров
@dependencies: abc, dataclasses, typing, asyncio
@created: 2025-09-20
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class AIResponse:
    """Структура ответа от AI сервиса."""

    content: str
    model: str
    tokens_used: int
    response_time: float
    provider: str
    cached: bool = False
    metadata: dict[str, Any] | None = None


@dataclass
class ConversationMessage:
    """Структура сообщения в диалоге."""

    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime | None = None


class AIProviderError(Exception):
    """Базовый класс для ошибок AI провайдеров."""

    def __init__(
        self, message: str, provider: str, error_code: str | None = None
    ) -> None:
        self.provider = provider
        self.error_code = error_code
        super().__init__(message)


class APIConnectionError(AIProviderError):
    """Ошибка подключения к API."""


class APIRateLimitError(AIProviderError):
    """Ошибка превышения лимита запросов."""


class APIAuthenticationError(AIProviderError):
    """Ошибка аутентификации."""


class APIQuotaExceededError(AIProviderError):
    """Ошибка превышения квоты/баланса."""


class BaseAIProvider(ABC):
    """Базовый абстрактный класс для всех AI провайдеров."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._client = None
        self._is_available = None
        self._last_health_check = None

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Название провайдера."""

    @abstractmethod
    async def generate_response(
        self,
        messages: list[ConversationMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AIResponse:
        """
        Генерация ответа от AI провайдера.

        Args:
            messages: Список сообщений диалога
            temperature: Температура генерации (0.0-2.0)
            max_tokens: Максимальное количество токенов
            **kwargs: Дополнительные параметры для конкретного провайдера

        Returns:
            AIResponse: Ответ от AI провайдера

        Raises:
            AIProviderError: При ошибках взаимодействия с API
        """

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """
        Проверка здоровья провайдера.

        Returns:
            dict: Статус и метрики провайдера
        """

    @abstractmethod
    async def close(self) -> None:
        """Закрытие соединений и освобождение ресурсов."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Проверка правильности настройки провайдера."""

    async def is_available(self) -> bool:
        """
        Проверка доступности провайдера.
        Кешируется на 60 секунд для избежания частых проверок.
        """
        now = datetime.now()

        # Проверяем кеш
        if (
            self._is_available is not None
            and self._last_health_check is not None
            and (now - self._last_health_check).total_seconds() < 60
        ):
            return self._is_available

        try:
            health_result = await asyncio.wait_for(self.health_check(), timeout=10.0)
            self._is_available = health_result.get("status") == "healthy"
        except Exception:
            self._is_available = False

        self._last_health_check = now
        return self._is_available

    def _prepare_messages(
        self,
        messages: list[ConversationMessage],
    ) -> list[dict[str, str]]:
        """Подготовка сообщений для API в стандартном формате OpenAI."""
        return [
            {
                "role": msg.role,
                "content": msg.content,
            }
            for msg in messages
        ]

    def _calculate_response_time(self, start_time: float) -> float:
        """Расчет времени ответа."""
        return asyncio.get_event_loop().time() - start_time

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.provider_name})"

    def __repr__(self) -> str:
        return self.__str__()


# Экспорт основных классов
__all__ = [
    "AIProviderError",
    "AIResponse",
    "APIAuthenticationError",
    "APIConnectionError",
    "APIQuotaExceededError",
    "APIRateLimitError",
    "BaseAIProvider",
    "ConversationMessage",
]
