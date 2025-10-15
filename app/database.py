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
from app.lexicon.gettext import get_log_text


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

    logger.info(get_log_text("database.db_connecting"))

    # Создаем движок с оптимизированными настройками пула соединений
    engine = create_async_engine(
        config.database.database_url,
        # Оптимизированные настройки пула соединений
        pool_size=20,  # Увеличиваем пул соединений с 10 до 20
        max_overflow=30,  # Увеличиваем дополнительные соединения с 20 до 30
        pool_timeout=30,  # Таймаут ожидания соединения
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
        get_log_text("database.db_engine_created").format(
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

    # Валидация имени БД для предотвращения SQL-инъекции
    import re

    invalid_database_name_error = "Invalid database name"
    if not re.match(r"^[a-zA-Z0-9_]+$", database_name):
        raise ValueError(invalid_database_name_error)

    logger.info(
        get_log_text("database.db_check_existence").format(database_name=database_name)
    )

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
                logger.info(
                    get_log_text("database.db_exists").format(
                        database_name=database_name
                    )
                )
            else:
                logger.info(
                    get_log_text("database.db_creating").format(
                        database_name=database_name
                    )
                )
                # Создаем базу данных (используем параметризованный запрос для безопасности)
                await conn.execute(f'CREATE DATABASE "{database_name}"')
                logger.info(
                    get_log_text("database.db_created").format(
                        database_name=database_name
                    )
                )

        finally:
            await conn.close()

    except Exception as e:
        logger.error(get_log_text("database.db_create_error").format(error=e))
        # Не поднимаем исключение, возможно БД уже существует
        logger.warning(get_log_text("database.db_continue_with_existing"))


async def create_tables_if_not_exist() -> None:
    """Создание таблиц если они не существуют."""
    logger.info(get_log_text("database.db_check_tables"))

    try:
        # Проверяем существование таблицы users
        async with get_session() as session:
            result = await session.execute(
                text(
                    "SELECT EXISTS ("
                    "SELECT FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = 'users'"
                    ")"
                )
            )
            table_exists = result.scalar()

            if table_exists:
                logger.info(get_log_text("database.db_tables_exist"))
            else:
                logger.info(get_log_text("database.db_creating_tables"))
                # Создаем таблицы
                async with _db_manager.get_engine().begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                logger.info(get_log_text("database.db_tables_created"))

    except Exception as e:
        logger.error(get_log_text("database.db_tables_check_error").format(error=e))


async def init_db() -> None:
    """
    Инициализация базы данных.
    Создает базу данных и таблицы если они не существуют.
    """

    try:
        logger.info(get_log_text("database.db_initializing"))

        # Создаем базу данных если не существует
        await create_database_if_not_exists()

        # Создаем движок
        engine = create_engine()
        _db_manager._engine = engine

        # Создаем фабрику сессий
        session_factory = create_session_factory(engine)
        _db_manager._session_factory = session_factory

        # Создаем таблицы если не существуют
        await create_tables_if_not_exist()

        logger.success(get_log_text("database.db_initialized"))

    except Exception as e:
        logger.error(get_log_text("database.db_init_error").format(error=e))
        raise


async def close_db() -> None:
    """Закрытие подключения к базе данных."""
    logger.info(get_log_text("database.db_closing"))

    if _db_manager._engine:
        await _db_manager._engine.dispose()
        logger.info(get_log_text("database.db_closed"))


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Контекстный менеджер для получения сессии базы данных.

    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy
    """

    if _db_manager._session_factory is None:
        msg = "База данных не инициализирована. Вызовите init_db() сначала."
        raise RuntimeError(msg)

    logger.info(get_log_text("database.db_new_session"))

    session = _db_manager._session_factory()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        if isinstance(e, SQLAlchemyError):
            logger.error(get_log_text("database.db_sqlalchemy_error").format(error=e))
        else:
            logger.error(get_log_text("database.db_unexpected_error").format(error=e))
        raise
    finally:
        await session.close()
        logger.info(get_log_text("database.db_session_closed"))


# Добавляем недостающие функции для тестов
async def check_connection() -> bool:
    """Проверка подключения к базе данных."""
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


async def create_tables() -> None:
    """Создание таблиц."""
    async with _db_manager.get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Удаление таблиц."""
    async with _db_manager.get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Получение фабрики сессий."""
    return _db_manager.get_session_factory()
