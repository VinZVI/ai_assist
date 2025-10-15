"""
@file: middleware/emotional_profiling.py
@description: Middleware для анализа эмоций пользователей и обновления их профилей
@dependencies: aiogram, loguru, app.services.user_service
@created: 2025-10-15
"""

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from aiogram.types import CallbackQuery, Message, TelegramObject
from aiogram.types import User as TelegramUser
from loguru import logger

from app.middleware.base import BaseAIMiddleware
from app.services.user_service import user_service

if TYPE_CHECKING:
    from app.models.user import User


class EmotionalProfilingMiddleware(BaseAIMiddleware):
    """Middleware для анализа эмоций пользователей и обновления их профилей."""

    def __init__(self) -> None:
        """Инициализация EmotionalProfilingMiddleware."""
        super().__init__()
        logger.info("EmotionalProfilingMiddleware инициализирован")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Обработка события с анализом эмоций пользователя.

        Args:
            handler: Следующий обработчик в цепочке
            event: Событие Telegram
            data: Данные контекста обработки

        Returns:
            Результат выполнения следующего обработчика
        """
        # Проверяем только текстовые сообщения
        if isinstance(event, Message) and event.text:
            telegram_user: TelegramUser | None = event.from_user
            if telegram_user:
                user_id = telegram_user.id
                user: User | None = data.get("user")

                if user:
                    # Анализируем сообщение пользователя и обновляем его эмоциональный профиль
                    await self._analyze_user_emotions(user, event.text)

        # Передаем управление следующему обработчику
        return await handler(event, data)

    async def _analyze_user_emotions(self, user: "User", message_text: str) -> None:
        """
        Анализ эмоций пользователя на основе его сообщения.

        Args:
            user: Пользователь
            message_text: Текст сообщения пользователя
        """
        try:
            # Простой анализ на основе ключевых слов (в реальной реализации можно использовать
            # более сложные методы анализа тональности)
            emotional_indicators = self._extract_emotional_indicators(message_text)

            # Обновляем эмоциональный профиль пользователя
            if emotional_indicators:
                await user_service.update_emotional_profile(
                    user.telegram_id, emotional_indicators
                )

                logger.debug(
                    f"Эмоциональный профиль обновлен для пользователя {user.telegram_id}: "
                    f"{emotional_indicators}"
                )
        except Exception as e:
            logger.warning(
                f"Ошибка при анализе эмоций пользователя {user.telegram_id}: {e}"
            )

    def _extract_emotional_indicators(self, text: str) -> dict[str, Any]:
        """
        Извлечение эмоциональных индикаторов из текста.

        Args:
            text: Текст для анализа

        Returns:
            dict: Эмоциональные индикаторы
        """
        # Приводим текст к нижнему регистру для анализа
        lower_text = text.lower()

        # Счетчики эмоциональных индикаторов
        indicators = {
            "positive_words": 0,
            "negative_words": 0,
            "neutral_words": 0,
            "intensity": 0,
            "topics": [],
        }

        # Позитивные слова
        positive_words = [
            "хорошо",
            "отлично",
            "прекрасно",
            "замечательно",
            "рад",
            "рада",
            "счастлив",
            "счастлива",
            "удовлетворен",
            "удовлетворена",
            "доволен",
            "довольна",
            "люблю",
            "прекрасный",
            "замечательный",
            "великолепный",
            "fantastic",
            "great",
            "wonderful",
            "amazing",
            "happy",
            "love",
            "excellent",
            "perfect",
            "awesome",
            "brilliant",
        ]

        # Негативные слова
        negative_words = [
            "плохо",
            "ужасно",
            "отвратительно",
            "грустно",
            "печально",
            "зло",
            "злой",
            "злая",
            "ненавижу",
            "страшно",
            "боюсь",
            "тревожно",
            "тревожный",
            "тревожная",
            "bad",
            "terrible",
            "awful",
            "sad",
            "horrible",
            "hate",
            "scary",
            "afraid",
            "anxious",
            "worried",
            "depressed",
            "angry",
            "mad",
            "upset",
            "disgusting",
        ]

        # Подсчитываем позитивные слова
        for word in positive_words:
            indicators["positive_words"] += lower_text.count(word)

        # Подсчитываем негативные слова
        for word in negative_words:
            indicators["negative_words"] += lower_text.count(word)

        # Определяем интенсивность (на основе восклицательных знаков и заглавных букв)
        indicators["intensity"] = (
            text.count("!") + sum(1 for c in text if c.isupper()) / len(text)
            if text
            else 0
        )

        # Определяем темы (простой подход)
        topics = []
        if any(
            word in lower_text for word in ["работа", "работу", "работы", "job", "work"]
        ):
            topics.append("work")
        if any(word in lower_text for word in ["семья", "семье", "семью", "family"]):
            topics.append("family")
        if any(
            word in lower_text
            for word in ["друзья", "друг", "подруга", "friends", "friend"]
        ):
            topics.append("social")
        if any(
            word in lower_text
            for word in ["здоровье", "здоров", "болезнь", "health", "ill", "sick"]
        ):
            topics.append("health")
        if any(
            word in lower_text
            for word in ["деньги", "денег", "заработок", "money", "finance"]
        ):
            topics.append("finance")
        if any(
            word in lower_text
            for word in ["любовь", "люблю", "романтика", "love", "romance"]
        ):
            topics.append("romance")

        indicators["topics"] = topics

        return indicators


# Экспорт для удобного использования
__all__ = [
    "EmotionalProfilingMiddleware",
]
