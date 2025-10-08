"""
@file: tests/integration/test_language_switching.py
@description: Тесты для проверки функциональности переключения языка
@dependencies: pytest, unittest.mock
@created: 2025-10-07
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, Message
from aiogram.types import User as TelegramUser
from sqlalchemy import update

from app.handlers.language import handle_language_selection
from app.lexicon.gettext import get_text


class TestLanguageSwitching:
    """Тесты для функциональности переключения языка."""

    @pytest.fixture
    def mock_callback(self) -> MagicMock:
        """Фикстура для создания мок-объекта callback запроса."""
        callback = MagicMock(spec=CallbackQuery)
        callback.data = "select_language:en"
        callback.from_user = TelegramUser(id=123456789, is_bot=False, first_name="Test")
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        return callback

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Фикстура для создания мок-объекта сессии базы данных."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_language_switching_success(self, mock_callback: MagicMock) -> None:
        """Тест успешного переключения языка."""
        # Мокаем сессию базы данных
        with patch("app.handlers.language.get_session") as mock_get_session:
            mock_session_context = AsyncMock()
            mock_session = AsyncMock()

            # Настраиваем мок для пользователя
            mock_user = MagicMock()
            mock_user.language_code = "en"

            # Настраиваем мок для результата запроса
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user

            # Настраиваем мок для execute
            mock_session.execute.return_value = mock_result
            mock_session_context.__aenter__.return_value = mock_session
            mock_get_session.return_value = mock_session_context

            # Мокаем update из sqlalchemy
            with patch("sqlalchemy.update"):
                # Выполняем тест
                await handle_language_selection(mock_callback)

                # Проверяем, что сообщение было отредактировано с правильным текстом на английском
                mock_callback.message.edit_text.assert_called_once()
                call_args = mock_callback.message.edit_text.call_args[0]
                assert (
                    "✅" in call_args[0]
                )  # Проверяем, что это сообщение об успешном изменении
                assert (
                    "English" in call_args[0]
                )  # Проверяем, что указан английский язык

                # Проверяем, что callback был отвечен
                mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_language_switching_russian(self) -> None:
        """Тест переключения на русский язык."""
        # Проверяем, что тексты на русском языке корректны
        russian_text = get_text("language.title", "ru")
        assert "Выбор языка" in russian_text

        main_menu_text = get_text("keyboards.main_menu", "ru")
        assert "Главное меню" in main_menu_text

    @pytest.mark.asyncio
    async def test_language_switching_english(self) -> None:
        """Тест переключения на английский язык."""
        # Проверяем, что тексты на английском языке корректны
        english_text = get_text("language.title", "en")
        assert "Language Selection" in english_text

        main_menu_text = get_text("keyboards.main_menu", "en")
        assert "Main Menu" in main_menu_text

    @pytest.mark.asyncio
    async def test_system_prompt_language_switching(self) -> None:
        """Тест переключения языка системного промпта."""
        from app.lexicon.ai_prompts import create_system_message

        # Проверяем русский промпт
        ru_prompt = create_system_message("ru")
        assert "эмоциональную поддержку" in ru_prompt.content
        assert "эмпатичный AI-помощник" in ru_prompt.content

        # Проверяем английский промпт
        en_prompt = create_system_message("en")
        assert "emotional support" in en_prompt.content
        assert "empathetic AI assistant" in en_prompt.content

        # Проверяем, что по умолчанию используется русский промпт
        default_prompt = create_system_message()
        assert "эмоциональную поддержку" in default_prompt.content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
