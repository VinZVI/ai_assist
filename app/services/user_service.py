"""
@file: services/user_service.py
@description: Сервис для управления пользователями и их эмоциональными профилями
@dependencies: sqlalchemy, loguru
@created: 2025-10-15
"""

from datetime import UTC, datetime
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import get_session
from app.models.user import User, UserCreate, UserUpdate


class UserService:
    """Сервис для управления пользователями и их эмоциональными профилями."""

    @staticmethod
    async def get_user_by_telegram_id(telegram_id: int) -> User | None:
        """
        Получение пользователя по Telegram ID.

        Args:
            telegram_id: ID пользователя в Telegram

        Returns:
            User | None: Пользователь или None, если не найден
        """
        async with get_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def create_user(user_data: UserCreate) -> User:
        """
        Создание нового пользователя.

        Args:
            user_data: Данные для создания пользователя

        Returns:
            User: Созданный пользователь

        Raises:
            IntegrityError: Если пользователь с таким Telegram ID уже существует
        """
        async with get_session() as session:
            user = User(
                telegram_id=user_data.telegram_id,
                username=user_data.username,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                language_code=user_data.language_code,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(f"Пользователь создан: {user.telegram_id}")
            return user

    @staticmethod
    async def update_user(telegram_id: int, user_data: UserUpdate) -> User | None:
        """
        Обновление данных пользователя.

        Args:
            telegram_id: ID пользователя в Telegram
            user_data: Данные для обновления

        Returns:
            User | None: Обновленный пользователь или None, если не найден
        """
        async with get_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return None

            # Обновляем поля пользователя
            update_data = user_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)

            user.updated_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(user)
            logger.info(f"Пользователь обновлен: {user.telegram_id}")
            return user

    @staticmethod
    async def update_emotional_profile(
        telegram_id: int, profile_data: dict[str, Any]
    ) -> User | None:
        """
        Обновление эмоционального профиля пользователя.

        Args:
            telegram_id: ID пользователя в Telegram
            profile_data: Данные эмоционального профиля

        Returns:
            User | None: Обновленный пользователь или None, если не найден
        """
        async with get_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return None

            user.update_emotional_profile(profile_data)
            user.updated_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(user)
            logger.info(f"Эмоциональный профиль обновлен для пользователя: {telegram_id}")
            return user

    @staticmethod
    async def update_support_preferences(
        telegram_id: int, preferences: dict[str, Any]
    ) -> User | None:
        """
        Обновление предпочтений в типе поддержки пользователя.

        Args:
            telegram_id: ID пользователя в Telegram
            preferences: Предпочтения в типе поддержки

        Returns:
            User | None: Обновленный пользователь или None, если не найден
        """
        async with get_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return None

            user.update_support_preferences(preferences)
            user.updated_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(user)
            logger.info(f"Предпочтения поддержки обновлены для пользователя: {telegram_id}")
            return user

    @staticmethod
    async def get_user_stats() -> dict[str, int]:
        """
        Получение статистики пользователей.

        Returns:
            dict: Статистика пользователей
        """
        async with get_session() as session:
            # Общее количество пользователей
            total_users_stmt = select(User)
            total_users_result = await session.execute(total_users_stmt)
            total_users = len(total_users_result.scalars().all())

            # Активные пользователи
            active_users_stmt = select(User).where(User.is_active == True)
            active_users_result = await session.execute(active_users_stmt)
            active_users = len(active_users_result.scalars().all())

            # Премиум пользователи
            premium_users_stmt = select(User).where(User.is_premium == True)
            premium_users_result = await session.execute(premium_users_stmt)
            premium_users = len(premium_users_result.scalars().all())

            return {
                "total_users": total_users,
                "active_users": active_users,
                "premium_users": premium_users,
            }


# Глобальный экземпляр сервиса
user_service = UserService()


# Экспорт для удобного использования
__all__ = [
    "UserService",
    "user_service",
]