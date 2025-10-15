"""
@file: services/user_service.py
@description: Сервис для управления пользователями и их эмоциональными профилями
@dependencies: sqlalchemy, loguru
@created: 2025-10-15
"""

import asyncio
from datetime import UTC, datetime
from typing import Any

from aiogram.types import Message
from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import get_session
from app.models.user import User, UserCreate, UserUpdate
from app.services.cache_service import cache_service


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
        # Пытаемся получить пользователя из кеша
        user = await cache_service.get_user(telegram_id)

        # Если нет в кеше, загружаем из БД
        if not user:
            async with get_session() as session:
                stmt = select(User).where(User.telegram_id == telegram_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                # Если пользователь найден в БД, кешируем его
                if user:
                    await cache_service.set_user(user)

        return user

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

            # Обновляем кеш
            await cache_service.set_user(user)

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

            # Обновляем кеш
            await cache_service.set_user(user)

            logger.info(
                f"Эмоциональный профиль обновлен для пользователя: {telegram_id}"
            )
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

            # Обновляем кеш
            await cache_service.set_user(user)

            logger.info(
                f"Предпочтения поддержки обновлены для пользователя: {telegram_id}"
            )
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
            active_users_stmt = select(User).where(User.is_active)
            active_users_result = await session.execute(active_users_stmt)
            active_users = len(active_users_result.scalars().all())

            # Премиум пользователи
            premium_users_stmt = select(User).where(User.is_premium)
            premium_users_result = await session.execute(premium_users_stmt)
            premium_users = len(premium_users_result.scalars().all())

            return {
                "total_users": total_users,
                "active_users": active_users,
                "premium_users": premium_users,
            }

    @staticmethod
    async def get_or_update_user(message: Message) -> User | None:
        """
        Получение или создание пользователя на основе сообщения.

        Args:
            message: Сообщение от пользователя Telegram

        Returns:
            User | None: Пользователь или None, если не удалось создать/получить
        """
        if not message.from_user:
            return None

        telegram_user = message.from_user
        async with get_session() as session:
            try:
                # Пытаемся найти пользователя по telegram_id
                stmt = select(User).where(User.telegram_id == telegram_user.id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                    # Обновляем информацию о пользователе если она изменилась
                    user_updated = False

                    if user.username != telegram_user.username:
                        user.username = telegram_user.username
                        user_updated = True

                    if user.first_name != telegram_user.first_name:
                        user.first_name = telegram_user.first_name
                        user_updated = True

                    if user.last_name != telegram_user.last_name:
                        user.last_name = telegram_user.last_name
                        user_updated = True

                    if user.language_code != telegram_user.language_code:
                        user.language_code = telegram_user.language_code
                        user_updated = True

                    # Сбрасываем дневной счетчик если прошел день
                    if user.reset_daily_count_if_needed():
                        user_updated = True

                    # Обновляем время последней активности
                    from datetime import UTC, datetime

                    user.last_activity_at = datetime.now(UTC)
                    user.updated_at = datetime.now(UTC)
                    user_updated = True

                    if user_updated:
                        session.add(user)
                        await session.commit()
                        await session.refresh(user)

                    return user
                # Создаем нового пользователя
                user_data = UserCreate(
                    telegram_id=telegram_user.id,
                    username=telegram_user.username,
                    first_name=telegram_user.first_name,
                    last_name=telegram_user.last_name,
                    language_code=telegram_user.language_code or "ru",
                )
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
                return user

            except Exception as e:
                from loguru import logger

                logger.error(f"Error in get_or_update_user: {e}")
                await session.rollback()
                return None

    @staticmethod
    async def update_user_activity_background(user_id: int) -> None:
        """
        Обновление активности пользователя в фоновом режиме.

        Args:
            user_id: ID пользователя в системе
        """
        try:
            # Не блокируем ответ пользователю, выполняем обновление в фоне
            asyncio.create_task(UserService._update_user_activity(user_id))
        except Exception as e:
            logger.error(
                f"Ошибка при запуске фонового обновления активности пользователя {user_id}: {e}"
            )

    @staticmethod
    async def _update_user_activity(user_id: int) -> None:
        """
        Внутренний метод для обновления активности пользователя.

        Args:
            user_id: ID пользователя в системе
        """
        try:
            async with get_session() as session:
                stmt = select(User).where(User.id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                    user.last_activity_at = datetime.now(UTC)
                    user.updated_at = datetime.now(UTC)
                    session.add(user)
                    await session.commit()
                    logger.debug(f"Активность пользователя {user_id} обновлена в фоне")
        except Exception as e:
            logger.error(
                f"Ошибка при фоновом обновлении активности пользователя {user_id}: {e}"
            )


# Глобальный экземпляр сервиса
user_service = UserService()


# Module-level function for backward compatibility
async def get_or_update_user(message: Message) -> User | None:
    """
    Получение или создание пользователя на основе сообщения.

    Args:
        message: Сообщение от пользователя Telegram

    Returns:
        User | None: Пользователь или None, если не удалось создать/получить
    """
    return await UserService.get_or_update_user(message)


# Экспорт для удобного использования
__all__ = [
    "UserService",
    "get_or_update_user",
    "user_service",
]
