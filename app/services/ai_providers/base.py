"""
@file: ai_providers/base.py
@description: Базовый абстрактный класс для всех AI провайдеров
@dependencies: abc, dataclasses, typing, asyncio
@created: 2025-09-20
"""

import asyncio
from abc import ABC, abstractmethod
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
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


@dataclass
class UserAIConversationContext:
    """Структура контекста диалога с 5 последними сообщениями пользователя и 5 последними ответами ИИ.

    Эта структура автоматически ограничивает количество сообщений каждого типа до 5,
    сохраняя только самые последние сообщения. Это позволяет эффективно управлять
    контекстом диалога без перегрузки памяти и обеспечивает оптимальную производительность ИИ.

    Атрибуты:
        user_messages: Список последних 5 сообщений пользователя
        ai_responses: Список последних 5 ответов ИИ
        last_interaction: Время последнего взаимодействия
        topics: Список обсуждаемых тем
        emotional_tone: Эмоциональный тон диалога
    """

    user_messages: list[ConversationMessage]  # Последние 5 сообщений пользователя
    ai_responses: list[ConversationMessage]  # Последние 5 ответов ИИ
    last_interaction: datetime | None = None
    topics: list[str] | None = None
    emotional_tone: str = "neutral"

    def __post_init__(self) -> None:
        """Инициализация после создания объекта."""
        if self.topics is None:
            self.topics = []
        if self.user_messages is None:
            self.user_messages = []
        if self.ai_responses is None:
            self.ai_responses = []

    def add_user_message(self, message: ConversationMessage) -> None:
        """Добавление сообщения пользователя с ограничением в 5 сообщений.

        Автоматически удаляет самые старые сообщения, если их количество
        превышает 5, сохраняя только последние.

        Args:
            message: Сообщение пользователя для добавления
        """
        self.user_messages.append(message)
        # Ограничиваем до 5 последних сообщений
        if len(self.user_messages) > 5:
            self.user_messages = self.user_messages[-5:]
        self.last_interaction = message.timestamp

    def add_ai_response(self, response: ConversationMessage) -> None:
        """Добавление ответа ИИ с ограничением в 5 ответов.

        Автоматически удаляет самые старые ответы, если их количество
        превышает 5, сохраняя только последние.

        Args:
            response: Ответ ИИ для добавления
        """
        self.ai_responses.append(response)
        # Ограничиваем до 5 последних ответов
        if len(self.ai_responses) > 5:
            self.ai_responses = self.ai_responses[-5:]
        self.last_interaction = response.timestamp

    def get_combined_history(self) -> list[ConversationMessage]:
        """Получение объединенной истории сообщений в хронологическом порядке.

        Объединяет сообщения пользователя и ответы ИИ в один список,
        отсортированный по времени создания сообщений.

        Returns:
            list[ConversationMessage]: Объединенная история в хронологическом порядке
        """
        # Объединяем все сообщения
        all_messages = self.user_messages + self.ai_responses
        # Сортируем по времени
        all_messages.sort(key=lambda x: x.timestamp or datetime.min.replace(tzinfo=UTC))
        return all_messages

    def to_dict(self) -> dict[str, Any]:
        """Преобразование контекста в словарь для сериализации.

        Преобразует контекст в формат, пригодный для сохранения в кэше
        или передачи по сети. Все datetime объекты преобразуются в ISO строки.

        Returns:
            dict: Словарь с данными контекста
        """
        return {
            "user_messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                }
                for msg in self.user_messages
            ],
            "ai_responses": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                }
                for msg in self.ai_responses
            ],
            "last_interaction": self.last_interaction.isoformat()
            if self.last_interaction
            else None,
            "topics": self.topics,
            "emotional_tone": self.emotional_tone,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserAIConversationContext":
        """Создание контекста из словаря.

        Восстанавливает контекст из словаря, полученного методом to_dict().
        Корректно обрабатывает преобразование строк ISO в datetime объекты.

        Args:
            data: Словарь с данными контекста

        Returns:
            UserAIConversationContext: Восстановленный контекст
        """

        def parse_message(msg_data: dict[str, Any]) -> ConversationMessage:
            timestamp = None
            if msg_data.get("timestamp"):
                with suppress(ValueError):
                    timestamp = datetime.fromisoformat(msg_data["timestamp"])
            return ConversationMessage(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=timestamp,
            )

        user_messages = [parse_message(msg) for msg in data.get("user_messages", [])]
        ai_responses = [parse_message(msg) for msg in data.get("ai_responses", [])]

        last_interaction = None
        if data.get("last_interaction"):
            with suppress(ValueError):
                last_interaction = datetime.fromisoformat(data["last_interaction"])

        return cls(
            user_messages=user_messages,
            ai_responses=ai_responses,
            last_interaction=last_interaction,
            topics=data.get("topics", []),
            emotional_tone=data.get("emotional_tone", "neutral"),
        )


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
            APIConnectionError: При ошибке подключения к API
            APIRateLimitError: При превышении лимита запросов
            APIAuthenticationError: При ошибке аутентификации
            APIQuotaExceededError: При превышении квоты/баланса
            AIProviderError: При других ошибках провайдера
        """

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """
        Проверка состояния провайдера.

        Returns:
            dict: Статус провайдера с ключами 'status' и 'details'
        """

    async def is_available(self) -> bool:
        """
        Проверка доступности провайдера с кэшированием результата.

        Returns:
            bool: True если провайдер доступен, False в противном случае
        """
        from datetime import UTC, datetime, timedelta

        now = datetime.now(UTC)
        # Проверяем кэш (1 минута)
        if self._last_health_check and (now - self._last_health_check) < timedelta(
            minutes=1
        ):
            return self._is_available if self._is_available is not None else False

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
    "UserAIConversationContext",
]
