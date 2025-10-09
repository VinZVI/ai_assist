"""
Тесты для проверки корректности системных сообщений AI.
"""

from app.lexicon.ai_prompts import create_system_message


class TestAIPrompts:
    """Тесты для проверки системных сообщений AI."""

    def test_create_system_message_russian(self) -> None:
        """Тест создания системного сообщения на русском языке."""
        # Act
        message = create_system_message("ru")

        # Assert
        assert message.role == "system"
        assert "эмоциональную поддержку" in message.content
        assert "Важные правила форматирования:" in message.content
        assert "4096 символов" in message.content
        assert "специальных символов" in message.content

    def test_create_system_message_english(self) -> None:
        """Тест создания системного сообщения на английском языке."""
        # Act
        message = create_system_message("en")

        # Assert
        assert message.role == "system"
        assert "emotional support" in message.content
        assert "Important formatting guidelines:" in message.content
        assert "4096 characters" in message.content
        assert "special characters" in message.content

    def test_create_system_message_default_language(self) -> None:
        """Тест создания системного сообщения с языком по умолчанию."""
        # Act
        message = create_system_message()

        # Assert
        assert message.role == "system"
        assert "эмоциональную поддержку" in message.content
        assert "Важные правила форматирования:" in message.content
