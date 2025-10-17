"""
Тесты для проверки импортов в модуле констант.
"""

from app.constants import (
    AI_ALL_PROVIDERS_FAILED,
    AI_AUTH_ERROR,
    AI_CONNECTION_ERROR,
    AI_EMPTY_RESPONSE_ERROR,
    AI_INVALID_RESPONSE_ERROR,
    AI_PROVIDER_ERROR,
    AI_QUOTA_ERROR,
    AI_RATE_LIMIT_ERROR,
    AI_TIMEOUT_ERROR,
    CONVERSATION_HISTORY_ERROR,
    CONVERSATION_SAVE_ERROR,
    DB_CONNECTION_ERROR,
    DB_INTEGRITY_ERROR,
    DB_SQLALCHEMY_ERROR,
    GENERAL_ERROR,
    UNEXPECTED_ERROR,
    USER_CREATION_ERROR,
    USER_NOT_FOUND_ERROR,
    USER_UPDATE_ERROR,
)


class TestConstantsImports:
    """Тесты для проверки импортов констант."""

    def test_constants_imports_work_correctly(self) -> None:
        """Тест, проверяющий, что все константы импортируются корректно."""
        # Проверяем, что все константы существуют и не равны None
        assert GENERAL_ERROR is not None
        assert UNEXPECTED_ERROR is not None
        assert DB_CONNECTION_ERROR is not None
        assert DB_INTEGRITY_ERROR is not None
        assert DB_SQLALCHEMY_ERROR is not None
        assert AI_PROVIDER_ERROR is not None
        assert AI_QUOTA_ERROR is not None
        assert AI_AUTH_ERROR is not None
        assert AI_RATE_LIMIT_ERROR is not None
        assert AI_CONNECTION_ERROR is not None
        assert AI_TIMEOUT_ERROR is not None
        assert AI_INVALID_RESPONSE_ERROR is not None
        assert AI_EMPTY_RESPONSE_ERROR is not None
        assert AI_ALL_PROVIDERS_FAILED is not None
        assert USER_NOT_FOUND_ERROR is not None
        assert USER_CREATION_ERROR is not None
        assert USER_UPDATE_ERROR is not None
        assert CONVERSATION_SAVE_ERROR is not None
        assert CONVERSATION_HISTORY_ERROR is not None

    def test_constants_have_correct_values(self) -> None:
        """Тест, проверяющий, что константы имеют правильные значения."""
        # Проверяем, что некоторые ключевые константы имеют ожидаемые значения
        assert "Произошла ошибка" in GENERAL_ERROR
        assert "AI провайдера" in AI_PROVIDER_ERROR
        assert "базе данных" in DB_CONNECTION_ERROR
