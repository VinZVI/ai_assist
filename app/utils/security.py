import os
import re

from loguru import logger


class SecurityValidator:
    """Валидатор безопасности конфигурации."""

    DANGEROUS_DEFAULTS = [
        "your_telegram_bot_token_here",
        "your_openrouter_api_key_here",
        "test_token",
        "placeholder",
        "changeme",
        "default",
        "example",
    ]

    @staticmethod
    def validate_production_token(token: str, token_type: str) -> tuple[bool, str]:
        """Валидация производственных токенов."""

        # Проверка на использование опасных значений по умолчанию
        if token.lower() in [d.lower() for d in SecurityValidator.DANGEROUS_DEFAULTS]:
            return (
                False,
                f"Production {token_type} token cannot use default/test values",
            )

        # Проверка окружения
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env in ["production", "prod"] and "test" in token.lower():
            return False, "Test tokens are not allowed in production environment"

        # Валидация формата токена Telegram
        if token_type == "telegram":
            if not re.match(r"^\d{8,10}:[A-Za-z0-9_-]{35}$", token):
                return False, "Invalid Telegram bot token format"

        # Валидация длины токенов API
        elif token_type == "api" and len(token) < 32:
            return False, "API token too short (minimum 32 characters)"

        return True, "Token is valid"

    @staticmethod
    def check_configuration_security(config_dict: dict) -> list[str]:
        """Проверка безопасности всей конфигурации."""
        issues = []

        # Проверка debug режима в production
        if config_dict.get("DEBUG", False) and os.getenv("ENVIRONMENT") == "production":
            issues.append("DEBUG mode is enabled in production")

        # Проверка стандартных паролей БД
        db_password = config_dict.get("DATABASE_PASSWORD", "")
        if db_password in ["password", "123456", "admin", "root"]:
            issues.append("Weak database password detected")

        return issues
