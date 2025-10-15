"""
@file: middleware/content_filter.py
@description: Middleware для фильтрации контента и обеспечения безопасности
@dependencies: aiogram, loguru, re
@created: 2025-10-15
"""

import re
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from aiogram.types import CallbackQuery, Message, TelegramObject
from aiogram.types import User as TelegramUser
from loguru import logger

from app.config import get_config
from app.lexicon.gettext import get_log_text, get_text
from app.middleware.base import BaseAIMiddleware

if TYPE_CHECKING:
    from app.models.user import User


class ContentFilterMiddleware(BaseAIMiddleware):
    """Middleware для фильтрации контента и обеспечения безопасности."""

    # Статистика по фильтрации контента
    _content_filter_stats: dict[str, int] = {
        "messages_filtered": 0,
        "users_warned": 0,
        "messages_blocked": 0,
    }

    def __init__(self) -> None:
        """Инициализация ContentFilterMiddleware."""
        super().__init__()
        self.config = get_config()
        logger.info(get_log_text("middleware.content_filter_middleware_initialized"))

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Обработка события с фильтрацией контента.

        Args:
            handler: Следующий обработчик в цепочке
            event: Событие Telegram
            data: Данные контекста обработки

        Returns:
            Результат выполнения следующего обработчика или None, если сообщение заблокировано
        """
        # Проверяем только текстовые сообщения
        if isinstance(event, Message) and event.text:
            telegram_user: TelegramUser | None = event.from_user
            if telegram_user:
                user_id = telegram_user.id
                user: User | None = data.get("user")
                user_lang = user.language_code if user else "ru"

                # Проверяем сообщение на запрещенный контент
                filter_result = self._filter_content(event.text)

                if filter_result["action"] == "block":
                    # Блокируем сообщение
                    self._content_filter_stats["messages_blocked"] += 1
                    logger.warning(
                        get_log_text("middleware.content_blocked").format(
                            user_id=user_id,
                            reason=filter_result["reason"],
                            content=event.text[:50]
                            + ("..." if len(event.text) > 50 else ""),
                        )
                    )

                    try:
                        await event.answer(
                            get_text(
                                "errors.content_blocked", user_lang or "ru"
                            ).format(reason=filter_result["reason"])
                        )
                    except Exception as e:
                        logger.warning(
                            get_log_text(
                                "middleware.content_filter_message_error"
                            ).format(error=str(e))
                        )

                    return None

                elif filter_result["action"] == "warn":
                    # Предупреждаем пользователя
                    self._content_filter_stats["messages_filtered"] += 1
                    logger.info(
                        get_log_text("middleware.content_warned").format(
                            user_id=user_id,
                            reason=filter_result["reason"],
                            content=event.text[:50]
                            + ("..." if len(event.text) > 50 else ""),
                        )
                    )

                    try:
                        await event.answer(
                            get_text(
                                "errors.content_warning", user_lang or "ru"
                            ).format(reason=filter_result["reason"])
                        )
                    except Exception as e:
                        logger.warning(
                            get_log_text(
                                "middleware.content_filter_message_error"
                            ).format(error=str(e))
                        )

        # Передаем управление следующему обработчику
        return await handler(event, data)

    def _filter_content(self, text: str) -> dict[str, str]:
        """
        Фильтрация контента на наличие запрещенных элементов.

        Args:
            text: Текст для фильтрации

        Returns:
            dict: Результат фильтрации с действием и причиной
        """
        # Приводим текст к нижнему регистру для проверки
        lower_text = text.lower()

        # Проверка на содержание персональных данных
        personal_data_patterns = [
            r"\b\d{11}\b",  # 11 цифр (возможный номер телефона)
            r"\b\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\b",  # Номер кредитной карты
            r"\b\d{16}\b",  # 16 цифр (возможный номер карты)
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
        ]

        for pattern in personal_data_patterns:
            if re.search(pattern, text):
                return {
                    "action": "warn",
                    "reason": get_text("errors.content_personal_data", "ru"),
                }

        # Проверка на содержание экстремистских материалов
        extremist_keywords = [
            "экстремизм",
            "терроризм",
            "насилие",
            "убийство",
            "самоубийство",
            "extremism",
            "terrorism",
            "violence",
            "murder",
            "suicide",
        ]

        for keyword in extremist_keywords:
            if keyword in lower_text:
                return {
                    "action": "block",
                    "reason": get_text("errors.content_extremist", "ru"),
                }

        # Проверка на содержание незаконных материалов
        illegal_keywords = [
            " нарко",
            " нарко",
            " нарко",  # Наркотики
            "drug",
            "narcotic",
            "illegal substance",
        ]

        for keyword in illegal_keywords:
            if keyword in lower_text:
                return {
                    "action": "block",
                    "reason": get_text("errors.content_illegal", "ru"),
                }

        # Если контент прошел все проверки
        return {"action": "allow", "reason": ""}

    @classmethod
    def get_content_filter_stats(cls) -> dict[str, int]:
        """
        Получение статистики фильтрации контента.

        Returns:
            Словарь со статистикой фильтрации контента
        """
        return cls._content_filter_stats.copy()

    @classmethod
    def reset_content_filter_stats(cls) -> None:
        """Сброс статистики фильтрации контента."""
        cls._content_filter_stats = {
            "messages_filtered": 0,
            "users_warned": 0,
            "messages_blocked": 0,
        }
