"""
Тесты для проверки оптимизации кэширования в user_service
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from app.models.user import User
from app.services.user_service import UserService


@pytest.mark.asyncio
async def test_update_emotional_profile_updates_cache() -> None:
    """Тест, проверяющий что update_emotional_profile обновляет кэш после обновления пользователя."""
    # Создаем тестового пользователя
    test_user = User(
        id=1,
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        language_code="ru",
    )

    # Мокаем сессию базы данных
    with patch("app.services.user_service.get_session") as mock_get_session:
        # Создаем мок контекстного менеджера сессии
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session_context)
        mock_session_context.__aexit__ = AsyncMock()
        mock_get_session.return_value = mock_session_context

        # Настраиваем мок execute так, чтобы он возвращал тестового пользователя
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = test_user
        mock_session_context.execute = AsyncMock(return_value=mock_result)

        # Мокаем cache_service
        with patch("app.services.user_service.cache_service") as mock_cache_service:
            mock_cache_service.set_user = AsyncMock()

            # Вызываем тестируемый метод
            profile_data = {"mood": "happy", "energy": "high"}
            result = await UserService.update_emotional_profile(123456789, profile_data)

            # Проверяем, что пользователь был обновлен
            assert result is not None
            # Note: We can't directly check emotional_profile since it's updated in place
            # and we're working with a mock object

            # Проверяем, что был сделан запрос к базе данных
            mock_session_context.execute.assert_called_once()
            executed_stmt = mock_session_context.execute.call_args[0][0]
            assert str(executed_stmt) == str(
                select(User).where(User.telegram_id == 123456789)
            )

            # Проверяем, что кэш был обновлен
            mock_cache_service.set_user.assert_called_once_with(test_user)

            # Проверяем, что сессия базы данных была использована для сохранения изменений
            mock_session_context.commit.assert_called_once()
            mock_session_context.refresh.assert_called_once_with(test_user)


@pytest.mark.asyncio
async def test_get_user_by_telegram_id_uses_cache() -> None:
    """Тест, проверяющий что get_user_by_telegram_id использует кэш."""
    # Создаем тестового пользователя
    test_user = User(
        id=1,
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        language_code="ru",
    )

    # Мокаем cache_service
    with patch("app.services.user_service.cache_service") as mock_cache_service:
        # Настраиваем мок кэша так, чтобы он возвращал пользователя
        mock_cache_service.get_user = AsyncMock(return_value=test_user)

        # Вызываем тестируемый метод
        result = await UserService.get_user_by_telegram_id(123456789)

        # Проверяем, что кэш был использован
        mock_cache_service.get_user.assert_called_once_with(123456789)

        # Проверяем, что пользователь был возвращен из кэша
        assert result is not None
        assert result.telegram_id == 123456789
        assert result.username == "testuser"


@pytest.mark.asyncio
async def test_get_user_by_telegram_id_fallback_to_db() -> None:
    """Тест, проверяющий что get_user_by_telegram_id обращается к БД, если пользователь не в кэше."""
    # Мокаем cache_service
    with patch("app.services.user_service.cache_service") as mock_cache_service:
        # Настраиваем мок кэша так, чтобы он не возвращал пользователя (имитируем промах кэша)
        mock_cache_service.get_user = AsyncMock(return_value=None)
        mock_cache_service.set_user = AsyncMock()

        # Создаем тестового пользователя
        test_user = User(
            id=1,
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User",
            language_code="ru",
        )

        # Мокаем сессию базы данных
        with patch("app.services.user_service.get_session") as mock_get_session:
            # Создаем мок контекстного менеджера сессии
            mock_session_context = AsyncMock()
            mock_session_context.__aenter__ = AsyncMock(
                return_value=mock_session_context
            )
            mock_session_context.__aexit__ = AsyncMock()
            mock_get_session.return_value = mock_session_context

            # Настраиваем мок execute так, чтобы он возвращал тестового пользователя
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = test_user
            mock_session_context.execute = AsyncMock(return_value=mock_result)

            # Вызываем тестируемый метод
            result = await UserService.get_user_by_telegram_id(123456789)

            # Проверяем, что кэш был проверен
            mock_cache_service.get_user.assert_called_once_with(123456789)

            # Проверяем, что был сделан запрос к базе данных
            mock_session_context.execute.assert_called_once()
            executed_stmt = mock_session_context.execute.call_args[0][0]
            assert str(executed_stmt) == str(
                select(User).where(User.telegram_id == 123456789)
            )

            # Проверяем, что пользователь был возвращен из БД
            assert result is not None
            assert result.telegram_id == 123456789
            assert result.username == "testuser"

            # Проверяем, что пользователь был добавлен в кэш
            mock_cache_service.set_user.assert_called_once_with(test_user)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
