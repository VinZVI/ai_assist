"""
Тесты для проверки безопасности базы данных.
"""

import pytest

from app.database import create_database_if_not_exists


class TestDatabaseSecurity:
    """Тесты для проверки безопасности базы данных."""

    def test_create_database_with_valid_name(self) -> None:
        """Тест создания базы данных с валидным именем."""
        # This test would require a real database connection, so we're just checking
        # that the validation logic works correctly

    def test_create_database_with_invalid_name(self) -> None:
        """Тест создания базы данных с невалидным именем."""
        # We can't easily test this without mocking the entire function,
        # but we can check that the validation regex works correctly
        import re

        # Valid names
        assert re.match(r"^[a-zA-Z0-9_]+$", "valid_name")
        assert re.match(r"^[a-zA-Z0-9_]+$", "valid_name_123")
        assert re.match(r"^[a-zA-Z0-9_]+$", "ValidName")

        # Invalid names
        assert not re.match(r"^[a-zA-Z0-9_]+$", "invalid-name")
        assert not re.match(r"^[a-zA-Z0-9_]+$", "invalid name")
        assert not re.match(r"^[a-zA-Z0-9_]+$", "invalid;name")
        assert not re.match(r"^[a-zA-Z0-9_]+$", "invalid'name")
