"""
@file: database.py
@description: Настройка подключения к базе данных с  # noqa: RUF002
              использованием SQLAlchemy async
@dependencies: sqlalchemy, asyncpg, loguru
@created: 2025-09-07
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import ClassVar
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
from app.log_lexicon.database import (
    DB_CHECK_EXISTENCE,
    DB_CHECK_TABLES,
    DB_CLOSED,
    DB_CLOSING,
    DB_CONNECTING,
    DB_CONNECTION_ERROR,
    DB_CONNECTION_OK,
    DB_CONTINUE_WITH_EXISTING,
    DB_CREATE_ERROR,
    DB_CREATED,
    DB_CREATING,
    DB_CREATING_TABLES,
    DB_ENGINE_CREATED,
    DB_EXISTS,
    DB_INIT_ERROR,
    DB_INITIALIZED,
    DB_NEW_SESSION,
    DB_SESSION_CLOSED,
    DB_SESSION_ENDED,
    DB_SQLALCHEMY_ERROR,
    DB_TABLES_CHECK_ERROR,
    DB_TABLES_CREATED,
    DB_TABLES_EXIST,
    DB_UNEXPECTED_ERROR,
)


class DatabaseManager:
    """Менеджер базы данных для управления подключением и сессиями."""

    _instance: ClassVar["DatabaseManager | None"] = None
    _engine: AsyncEngine | None = None
    _session_factory: async_sessionmaker[AsyncSession] | None = None

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_engine(self) -> AsyncEngine:
        """Получение экземпляра движка базы данных."""
        if self._engine is None:
            msg = "База данных не инициализирована. Вызовите init_db() сначала."
            raise RuntimeError(msg)
        return self._engine

    def get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Получение фабрики сессий."""
        if self._session_factory is None:
            msg = "База данных не инициализирована. Вызовите init_db() сначала."
            raise RuntimeError(msg)
        return self._session_factory

    def reset(self) -> None:
        """Сброс состояния менеджера базы данных (для тестирования)."""
        self._engine = None
        self._session_factory = None


# Глобальный экземпляр менеджера базы данных
_db_manager = DatabaseManager()

# Базовый класс для всех моделей
Base = declarative_base()


def create_engine() -> AsyncEngine:
    """Создание асинхронного движка SQLAlchemy."""
    config = get_config()

    logger.info(DB_CONNECTING)

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
        DB_ENGINE_CREATED.format(
            db_url=config.database.database_url.split("@")[1]
            if "@" in config.database.database_url
            else "скрыт"
        )
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

    logger.info(DB_CHECK_EXISTENCE.format(database_name=database_name))

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
                logger.info(DB_EXISTS.format(database_name=database_name))
            else:
                logger.info(DB_CREATING.format(database_name=database_name))
                # Создаем базу данных
                await conn.execute(f'CREATE DATABASE "{database_name}"')
                logger.info(DB_CREATED.format(database_name=database_name))

        finally:
            await conn.close()

    except Exception as e:
        logger.error(DB_CREATE_ERROR.format(error=e))
        # Не поднимаем исключение, возможно БД уже существует
        logger.warning(DB_CONTINUE_WITH_EXISTING)


async def create_tables_if_not_exist() -> None:
    """Создание таблиц если они не существуют."""
    logger.info(DB_CHECK_TABLES)

    try:
        # Проверяем существование таблицы users
        async with get_session() as session:
            result = await session.execute(
                text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables "
                    "WHERE table_name = 'users')"
                )
            )
            tables_exist = result.scalar()

        if tables_exist:
            logger.info(DB_TABLES_EXIST)
        else:
            logger.info(DB_CREATING_TABLES)
            await create_tables()
            logger.info(DB_TABLES_CREATED)

    except Exception as e:
        logger.warning(DB_TABLES_CHECK_ERROR.format(error=e))
        await create_tables()


async def init_db() -> None:
    """Инициализация базы данных."""
    try:
        # Сначала создаем базу данных если её нет
        await create_database_if_not_exists()

        # Создаем движок
        _db_manager._engine = create_engine()

        # Создаем фабрику сессий
        _db_manager._session_factory = create_session_factory(_db_manager._engine)

        # Проверяем подключение
        await check_connection()

        # Автоматически создаем таблицы если их нет
        await create_tables_if_not_exist()

        logger.info(DB_INITIALIZED)

    except Exception as e:
        logger.error(DB_INIT_ERROR.format(error=e))
        raise


async def close_db() -> None:
    """Закрытие подключения к базе данных."""
    if _db_manager._engine:
        logger.info(DB_CLOSING)
        await _db_manager._engine.dispose()
        _db_manager._engine = None
        _db_manager._session_factory = None
        logger.info(DB_CLOSED)


async def check_connection() -> bool:
    """Проверка подключения к базе данных."""
    try:
        async with get_session() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            logger.info(DB_CONNECTION_OK)
            return True
    except Exception as e:
        logger.error(DB_CONNECTION_ERROR.format(error=e))
        return False


def get_engine() -> AsyncEngine:
    """Получение экземпляра движка базы данных."""
    return _db_manager.get_engine()


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Получение фабрики сессий."""
    return _db_manager.get_session_factory()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Контекстный менеджер для получения сессии базы данных.

    Использование:
        async with get_session() as session:
            user = await session.get(User, user_id)
            # ... работа с базой данных  # noqa: RUF002
            await session.commit()
    """
    session_factory = get_session_factory()
    session = session_factory()

    try:
        logger.debug(DB_NEW_SESSION)
        yield session
        await session.commit()
        logger.debug(DB_SESSION_ENDED)

    except SQLAlchemyError as e:
        logger.error(DB_SQLALCHEMY_ERROR.format(error=e))
        await session.rollback()
        raise

    except Exception as e:
        logger.error(DB_UNEXPECTED_ERROR.format(error=e))
        await session.rollback()
        raise

    finally:
        await session.close()
        logger.debug(DB_SESSION_CLOSED)


async def create_tables() -> None:
    """Создание всех таблиц в базе данных."""
    logger.info(DB_CREATING_TABLES)

    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info(DB_TABLES_CREATED)

    except Exception as e:
        logger.error(DB_CREATE_ERROR.format(error=e))
        raise


async def drop_tables() -> None:
    """Удаление всех таблиц из базы данных (только для разработки!)."""
    config = get_config()

    if not config.debug:
        msg = "Удаление таблиц разрешено только в debug режиме!"
        raise RuntimeError(msg)

    logger.warning("⚠️ Удаление всех таблиц из базы данных...")

    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        logger.warning("🗑️ Все таблицы удалены")

    except Exception as e:
        logger.error(DB_CREATE_ERROR.format(error=e))
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
