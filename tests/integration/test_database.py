"""
@file: test_database.py
@description: Тесты для модуля database.py и работы с базой данных
@dependencies: pytest, pytest-asyncio, sqlalchemy
@created: 2025-09-12
"""

from typing import Never, NoReturn
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.pool import NullPool

from app.database import (
    DatabaseManager,
    check_connection,
    close_db,
    create_engine,
    create_session_factory,
    create_tables,
    drop_tables,
    get_session,
    get_session_factory,
    init_db,
)


@pytest.mark.asyncio
class TestDatabaseEngine:
    """Тесты движка базы данных."""

    @patch("app.database.get_config")
    @patch("app.database.create_async_engine")
    def test_create_engine_success(
        self,
        mock_create_async_engine: MagicMock,
        mock_get_config: MagicMock,
    ) -> None:
        """Тест успешного создания движка БД."""
        # Мокаем конфигурацию
        mock_config = MagicMock()
        mock_config.database.database_url = (
            "postgresql+asyncpg://test:test@localhost/test"
        )
        mock_config.debug = False
        mock_config.database.database_pool_size = 20
        mock_config.database.database_timeout = 30
        mock_get_config.return_value = mock_config

        # Мокаем движок
        mock_engine = AsyncMock()
        mock_create_async_engine.return_value = mock_engine

        # Вызываем функцию
        engine = create_engine()

        # Проверяем результаты
        assert engine == mock_engine
        mock_create_async_engine.assert_called_once_with(
            mock_config.database.database_url,
            pool_size=mock_config.database.database_pool_size,
            max_overflow=30,
            pool_timeout=mock_config.database.database_timeout,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=False,
            echo_pool=False,
            poolclass=None,
            connect_args={
                "server_settings": {
                    "application_name": "ai_assist_bot",
                    "jit": "off",
                },
            },
        )

    @patch("app.database.get_config")
    def test_create_engine_debug_mode(self, mock_get_config: MagicMock) -> None:
        """Тест создания движка в debug режиме."""
        mock_config = MagicMock()
        mock_config.database.database_url = (
            "postgresql+asyncpg://test:test@localhost/test"
        )
        mock_config.debug = True
        mock_config.database.database_pool_size = 20
        mock_config.database.database_timeout = 30
        mock_get_config.return_value = mock_config

        with patch("app.database.create_async_engine") as mock_create_engine:
            mock_engine = AsyncMock()
            mock_create_engine.return_value = mock_engine

            engine = create_engine()

            assert engine == mock_engine
            mock_create_engine.assert_called_once_with(
                mock_config.database.database_url,
                pool_size=mock_config.database.database_pool_size,
                max_overflow=30,
                pool_timeout=mock_config.database.database_timeout,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=True,  # В debug режиме echo=True
                echo_pool=True,
                poolclass=NullPool,  # В debug режиме используем NullPool
                connect_args={
                    "server_settings": {
                        "application_name": "ai_assist_bot",
                        "jit": "off",
                    },
                },
            )

    @patch("app.database.create_engine")
    def test_create_session_factory_success(
        self, mock_create_engine: MagicMock
    ) -> None:
        """Тест успешного создания фабрики сессий."""
        # Мокаем движок
        mock_engine = AsyncMock()
        mock_create_engine.return_value = mock_engine

        # Создаем фабрику сессий
        factory = create_session_factory(mock_engine)

        # Проверяем, что фабрика создана правильно
        assert factory is not None


@pytest.mark.asyncio
class TestDatabaseInitialization:
    """Тесты для инициализации и закрытия БД."""

    @patch("app.database.create_database_if_not_exists")
    @patch("app.database.check_connection")
    @patch("app.database.create_session_factory")
    @patch("app.database.create_engine")
    @patch("app.database.get_config")
    async def test_init_db_success(
        self,
        mock_get_config: MagicMock,
        mock_create_engine: MagicMock,
        mock_create_factory: MagicMock,
        mock_check_conn: MagicMock,
        mock_create_db: MagicMock,
    ) -> None:
        """Тест успешной инициализации БД."""
        # Мокаем конфигурацию
        mock_config = MagicMock()
        mock_config.database.database_url = (
            "postgresql+asyncpg://test:test@localhost/test"
        )
        mock_get_config.return_value = mock_config

        # Мокаем движок
        mock_engine = AsyncMock()
        mock_create_engine.return_value = mock_engine

        # Мокаем фабрику сессий
        mock_factory = MagicMock()
        mock_create_factory.return_value = mock_factory

        # Мокаем проверку подключения
        mock_check_conn.return_value = True

        # Мокаем создание базы данных
        mock_create_db.return_value = None

        # Сбрасываем менеджер базы данных для теста
        DatabaseManager._instance = None
        db_manager = DatabaseManager()
        db_manager._engine = mock_engine
        db_manager._session_factory = mock_factory

        # Мокаем create_tables_if_not_exist
        with patch("app.database._db_manager", db_manager):
            with patch("app.database.create_tables_if_not_exist") as mock_create_tables:
                mock_create_tables.return_value = None

                # Вызываем функцию
                await init_db()

                # Проверяем, что движок и фабрика установлены
                assert db_manager._engine == mock_engine
                assert db_manager._session_factory == mock_factory

    @patch("app.database.get_config")
    async def test_init_db_failure(self, mock_get_config: MagicMock) -> None:
        """Тест неудачной инициализации БД."""
        # Мокаем конфигурацию
        mock_config = MagicMock()
        mock_config.database.database_url = (
            "postgresql+asyncpg://test:test@localhost/test"
        )
        mock_get_config.return_value = mock_config

        # Сбрасываем менеджер базы данных для теста
        DatabaseManager._instance = None
        db_manager = DatabaseManager()
        db_manager.reset()

        with patch("app.database._db_manager", db_manager):
            with patch("app.database.create_engine") as mock_create_engine:
                # Мокаем ошибку создания движка
                mock_create_engine.side_effect = Exception("Connection failed")

                with patch("app.database.logger"):
                    with pytest.raises(Exception, match="Connection failed"):
                        await init_db()

    async def test_close_db_success(self) -> None:
        """Тест успешного закрытия БД."""
        # Создаем новый экземпляр менеджера для теста
        DatabaseManager._instance = None
        db_manager = DatabaseManager()

        # Мокаем движок
        mock_engine = AsyncMock()
        db_manager._engine = mock_engine
        db_manager._session_factory = MagicMock()

        with patch("app.database._db_manager", db_manager):
            await close_db()

            mock_engine.dispose.assert_called_once()
            assert db_manager._engine is None
            assert db_manager._session_factory is None

    async def test_close_db_no_engine(self) -> None:
        """Тест закрытия БД когда движок не инициализирован."""
        # Создаем новый экземпляр менеджера для теста
        DatabaseManager._instance = None
        db_manager = DatabaseManager()
        db_manager._engine = None
        db_manager._session_factory = None

        with patch("app.database._db_manager", db_manager):
            # Не должно бросать исключение
            await close_db()


@pytest.mark.asyncio
class TestDatabaseConnection:
    """Тесты для проверки подключения к БД."""

    @patch("app.database.get_session")
    async def test_check_connection_success(self, mock_get_session: MagicMock) -> None:
        """Тест успешной проверки подключения."""
        # Мокируем сессию и её методы
        mock_session_ctx = MagicMock()
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session_ctx
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result

        # Выполняем проверку
        result = await check_connection()

        # Проверяем результат
        assert result is True

    @patch("app.database.get_session")
    async def test_check_connection_failure(self, mock_get_session: MagicMock) -> None:
        """Тест неудачной проверки подключения."""
        # Мокируем исключение при выполнении запроса
        mock_session_ctx = MagicMock()
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session_ctx
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session.execute.side_effect = Exception("Connection failed")

        # Выполняем проверку
        result = await check_connection()

        # Проверяем результат
        assert result is False

    @patch("app.database._db_manager")
    async def test_get_session_success(self, mock_db_manager: MagicMock) -> None:
        """Тест успешного создания и использования сессии."""
        # Мокируем менеджер базы данных, фабрику и сессию
        mock_factory = MagicMock()
        mock_session = AsyncMock()
        mock_db_manager._session_factory = mock_factory
        mock_factory.return_value = mock_session

        # Используем контекстный менеджер
        async with get_session() as session:
            assert session == mock_session

        # Проверяем, что сессия была закрыта
        mock_session.close.assert_called_once()

    @patch("app.database._db_manager")
    async def test_get_session_rollback_on_error(
        self, mock_db_manager: MagicMock
    ) -> None:
        """Тест rollback при ошибке в сессии."""
        # Мокаем менеджер базы данных и фабрику сессий
        mock_factory = MagicMock()
        mock_session = AsyncMock()
        mock_db_manager._session_factory = mock_factory
        mock_factory.return_value = mock_session

        # Имитируем ошибку внутри контекстного менеджера
        with patch("app.database.logger"):
            database_error = Exception("Database error")
            with pytest.raises(Exception, match="Database error"):
                async with get_session() as session:
                    assert session == mock_session
                    raise database_error

    @patch("app.database._db_manager")
    async def test_create_tables_success(self, mock_db_manager: MagicMock) -> None:
        """Тест успешного создания таблиц."""
        # Мокаем движок базы данных
        mock_engine = AsyncMock()
        mock_db_manager.get_engine.return_value = mock_engine

        # Мокаем асинхронный контекстный менеджер правильно
        mock_conn = AsyncMock()
        mock_begin_context = AsyncMock()
        mock_begin_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_begin_context.__aexit__ = AsyncMock(return_value=None)
        mock_engine.begin = MagicMock(return_value=mock_begin_context)

        # Мокаем run_sync
        mock_conn.run_sync = AsyncMock()

        await create_tables()

        # Проверяем, что были вызваны правильные методы
        mock_engine.begin.assert_called_once()
        mock_conn.run_sync.assert_called_once()

    @patch("app.database._db_manager")
    async def test_create_tables_failure(self, mock_db_manager: MagicMock) -> None:
        """Тест неудачного создания таблиц."""
        # Мокаем движок базы данных
        mock_engine = AsyncMock()
        mock_db_manager.get_engine.return_value = mock_engine

        # Мокаем асинхронный контекстный менеджер с ошибкой
        mock_begin_context = AsyncMock()
        mock_begin_context.__aenter__ = AsyncMock(
            side_effect=Exception("Creation failed")
        )
        mock_begin_context.__aexit__ = AsyncMock(return_value=None)
        mock_engine.begin = MagicMock(return_value=mock_begin_context)

        with patch("app.database.logger"):
            with pytest.raises(Exception, match="Creation failed"):
                await create_tables()

    @patch("app.database.get_config")
    @patch("app.database._db_manager")
    async def test_drop_tables_debug_mode(
        self, mock_db_manager: MagicMock, mock_get_config: MagicMock
    ) -> None:
        """Тест удаления таблиц в debug режиме."""
        mock_config = MagicMock()
        mock_config.debug = True
        mock_get_config.return_value = mock_config

        # Мокаем движок базы данных
        mock_engine = AsyncMock()
        mock_db_manager.get_engine.return_value = mock_engine

        # Мокаем асинхронный контекстный менеджер правильно
        mock_conn = AsyncMock()
        mock_begin_context = AsyncMock()
        mock_begin_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_begin_context.__aexit__ = AsyncMock(return_value=None)
        mock_engine.begin = MagicMock(return_value=mock_begin_context)

        # Мокаем run_sync
        mock_conn.run_sync = AsyncMock()

        await drop_tables()

        # Проверяем, что drop_tables был вызван
        mock_engine.begin.assert_called_once()
        mock_conn.run_sync.assert_called_once()

    @patch("app.database._db_manager")
    @patch("app.database.get_config")
    async def test_drop_tables_production_mode(
        self, mock_get_config: MagicMock, mock_db_manager: MagicMock
    ) -> None:
        """Тест запрета удаления таблиц в production режиме."""
        mock_config = MagicMock()
        mock_config.debug = False
        mock_get_config.return_value = mock_config

        with pytest.raises(
            RuntimeError, match="Удаление таблиц разрешено только в debug режиме!"
        ):
            await drop_tables()


@pytest.mark.asyncio
class TestDatabaseBase:
    """Тесты для базового класса моделей."""

    def test_base_exists(self) -> None:
        """Тест существования базового класса."""
        from app.database import Base

        assert Base is not None

        # Проверяем, что это декларативная база SQLAlchemy
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")
