"""
@file: database.py
@description: Настройка подключения к базе данных с использованием SQLAlchemy async
@dependencies: sqlalchemy, asyncpg, loguru
@created: 2025-09-12
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import asyncpg
from loguru import logger
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool

from app.config import get_config

# Базовый класс для всех моделей
Base = declarative_base()

# Глобальные переменные для движка и сессии
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def create_engine() -> AsyncEngine:
    """Создание асинхронного движка SQLAlchemy."""
    config = get_config()

    logger.info("🔗 Создание подключения к базе данных...")

    # Создаем движок с настройками пула соединений
    engine = create_async_engine(
        config.database.database_url,
        # Настройки пула соединений
        pool_size=config.database.database_pool_size,
        max_overflow=20,
        pool_timeout=config.database.database_timeout,
        pool_recycle=3600,  # Пересоздание соединений каждый час
        pool_pre_ping=True,  # Проверка соединений перед использованием
        # Настройки для разработки
        echo=config.debug,  # Логирование SQL запросов в debug режиме
        echo_pool=config.debug,
        # Дополнительные настройки
        poolclass=NullPool if config.debug else None,  # Отключаем пул в debug режиме
        connect_args={
            "server_settings": {
                "application_name": "ai_assist_bot",
                "jit": "off",  # Отключаем JIT для стабильности
            },
        },
    )

    logger.info(
        f"✅ Движок базы данных создан: {config.database.database_url.split('@')[1] if '@' in config.database.database_url else 'скрыт'}"
    )
    return engine


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Создание фабрики сессий."""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Не сбрасываем объекты после commit
        autoflush=True,  # Автоматический flush перед query
        autocommit=False,
    )


async def create_database_if_not_exists() -> None:
    """Создание базы данных если она не существует."""
    config = get_config()

    # Парсим URL подключения
    parsed_url = urlparse(config.database.database_url)

    # Извлекаем параметры подключения
    host = parsed_url.hostname or "localhost"
    port = parsed_url.port or 5432
    username = parsed_url.username or "postgres"
    password = parsed_url.password or "password"
    database_name = parsed_url.path.lstrip("/") or "ai_assist"

    logger.info(f"🔍 Проверка существования базы данных '{database_name}'...")

    try:
        # Подключаемся к postgres БД для создания нашей БД
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database="postgres",  # Подключаемся к системной БД
        )

        try:
            # Проверяем существование базы данных
            result = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", database_name
            )

            if result:
                logger.info(f"✅ База данных '{database_name}' уже существует")
            else:
                logger.info(f"🏗️ Создание базы данных '{database_name}'...")
                # Создаем базу данных
                await conn.execute(f'CREATE DATABASE "{database_name}"')
                logger.info(f"✅ База данных '{database_name}' создана успешно")

        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"❌ Ошибка при создании базы данных: {e}")
        # Не поднимаем исключение, возможно БД уже существует
        logger.warning("⚠️ Продолжаем с существующей конфигурацией БД")


async def create_tables_if_not_exist() -> None:
    """Создание таблиц если они не существуют."""
    logger.info("🔍 Проверка существования таблиц...")

    try:
        # Проверяем существование таблицы users
        async with get_session() as session:
            result = await session.execute(
                text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
                )
            )
            tables_exist = result.scalar()

        if tables_exist:
            logger.info("✅ Таблицы уже существуют")
        else:
            logger.info("🏗️ Создание таблиц в базе данных...")
            await create_tables()
            logger.info("✅ Таблицы созданы успешно")

    except Exception as e:
        logger.warning(f"⚠️ Не удалось проверить таблицы, создаем заново: {e}")
        await create_tables()


async def init_db() -> None:
    """Инициализация базы данных."""
    global _engine, _session_factory

    try:
        # Сначала создаем базу данных если её нет
        await create_database_if_not_exists()

        # Создаем движок
        _engine = create_engine()

        # Создаем фабрику сессий
        _session_factory = create_session_factory(_engine)

        # Проверяем подключение
        await check_connection()

        # Автоматически создаем таблицы если их нет
        await create_tables_if_not_exist()

        logger.info("🎉 База данных инициализирована успешно")

    except Exception as e:
        logger.error(f"❌ Ошибка инициализации базы данных: {e}")
        raise


async def close_db() -> None:
    """Закрытие подключения к базе данных."""
    global _engine, _session_factory

    if _engine:
        logger.info("🔌 Закрытие подключения к базе данных...")
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("✅ Подключение к базе данных закрыто")


async def check_connection() -> bool:
    """Проверка подключения к базе данных."""
    try:
        async with get_session() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            logger.info("✅ Подключение к базе данных работает")
            return True
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        return False


def get_engine() -> AsyncEngine:
    """Получение экземпляра движка базы данных."""
    if _engine is None:
        raise RuntimeError(
            "База данных не инициализирована. Вызовите init_db() сначала."
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Получение фабрики сессий."""
    if _session_factory is None:
        raise RuntimeError(
            "База данных не инициализирована. Вызовите init_db() сначала."
        )
    return _session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Контекстный менеджер для получения сессии базы данных.

    Использование:
        async with get_session() as session:
            user = await session.get(User, user_id)
            # ... работа с базой данных
            await session.commit()
    """
    session_factory = get_session_factory()
    session = session_factory()

    try:
        logger.debug("📖 Создана новая сессия базы данных")
        yield session
        await session.commit()
        logger.debug("✅ Сессия базы данных закончена успешно")

    except SQLAlchemyError as e:
        logger.error(f"❌ Ошибка SQLAlchemy: {e}")
        await session.rollback()
        raise

    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка в сессии БД: {e}")
        await session.rollback()
        raise

    finally:
        await session.close()
        logger.debug("🔒 Сессия базы данных закрыта")


async def create_tables() -> None:
    """Создание всех таблиц в базе данных."""
    logger.info("🏗️ Создание таблиц в базе данных...")

    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ Все таблицы созданы успешно")

    except Exception as e:
        logger.error(f"❌ Ошибка создания таблиц: {e}")
        raise


async def drop_tables() -> None:
    """Удаление всех таблиц из базы данных (только для разработки!)."""
    config = get_config()

    if not config.debug:
        raise RuntimeError("Удаление таблиц разрешено только в debug режиме!")

    logger.warning("⚠️ Удаление всех таблиц из базы данных...")

    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        logger.warning("🗑️ Все таблицы удалены")

    except Exception as e:
        logger.error(f"❌ Ошибка удаления таблиц: {e}")
        raise


# Экспорт для удобного использования
__all__ = [
    "Base",
    "check_connection",
    "close_db",
    "create_tables",
    "drop_tables",
    "get_engine",
    "get_session",
    "get_session_factory",
    "init_db",
]
