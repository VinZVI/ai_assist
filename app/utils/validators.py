import html
import re
from typing import Any


class InputValidator:
    """Валидатор пользовательских входов для предотвращения инъекций и переполнения буферов."""

    MAX_MESSAGE_LENGTH = 4000
    MAX_RESPONSE_LENGTH = 8000
    MAX_USERNAME_LENGTH = 32

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Очистка текста от потенциально опасных символов."""
        if not text:
            return ""

        # HTML экранирование
        sanitized = html.escape(text.strip())

        # Удаление потенциально опасных последовательностей
        dangerous_patterns = [
            r"<script.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"data:text/html",
        ]

        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        return sanitized

    @staticmethod
    def validate_message_length(
        message: str, max_length: int | None = None
    ) -> tuple[bool, str]:
        """Валидация длины сообщения."""
        max_len = max_length or InputValidator.MAX_MESSAGE_LENGTH

        if not message or not message.strip():
            return False, "Сообщение не может быть пустым"

        if len(message) > max_len:
            return False, f"Сообщение слишком длинное (максимум {max_len} символов)"

        return True, ""

    @staticmethod
    def validate_user_data(telegram_user_data: dict) -> dict:
        """Валидация данных пользователя из Telegram."""
        validated = {}

        # Валидация username
        if telegram_user_data.get("username"):
            username = telegram_user_data["username"][
                : InputValidator.MAX_USERNAME_LENGTH
            ]
            validated["username"] = re.sub(r"[^\w]", "", username)

        # Валидация имени
        for field in ["first_name", "last_name"]:
            if telegram_user_data.get(field):
                name = InputValidator.sanitize_text(telegram_user_data[field])
                validated[field] = name[:50]  # Ограничение длины имени

        return validated
