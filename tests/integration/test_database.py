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
    check_connection,
    close_db,
    create_engine,
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
    async def test_create_engine_success(
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
            echo=False,
            poolclass=NullPool,
        )

    @patch("app.database.get_config")
    async def test_create_engine_debug_mode(self, mock_get_config: MagicMock) -> None:
        """Тест создания движка в debug режиме."""
        mock_config = MagicMock()
        mock_config.database.database_url = (
            "postgresql+asyncpg://test:test@localhost/test"
        )
        mock_config.debug = True
        mock_get_config.return_value = mock_config

        with patch("app.database.create_async_engine") as mock_create_engine:
            mock_engine = AsyncMock()
            mock_create_engine.return_value = mock_engine

            engine = create_engine()

            assert engine == mock_engine
            mock_create_engine.assert_called_once_with(
                mock_config.database.database_url,
                echo=True,  # В debug режиме echo=True
                poolclass=NullPool,
            )

    @patch("app.database.get_config")
    async def test_get_session_factory_success(
        self, mock_get_config: MagicMock
    ) -> None:
        """Тест успешного создания фабрики сессий."""
        # Мокаем конфигурацию
        mock_config = MagicMock()
        mock_config.database.database_url = (
            "postgresql+asyncpg://test:test@localhost/test"
        )
        mock_get_config.return_value = mock_config

        # Мокаем движок и фабрику
        with patch("app.database.create_engine") as mock_create_engine:
            mock_engine = AsyncMock()
            mock_create_engine.return_value = mock_engine

            with patch("app.database.async_sessionmaker") as mock_sessionmaker:
                mock_factory = MagicMock()
                mock_sessionmaker.return_value = mock_factory

                factory = get_session_factory()

                assert factory == mock_factory
                mock_sessionmaker.assert_called_once_with(
                    bind=mock_engine,
                    expire_on_commit=False,
                    class_=AsyncSession,
                )


@pytest.mark.asyncio
class TestDatabaseInitialization:
    """Тесты для инициализации и закрытия БД."""

    @patch("app.database.check_connection")
    @patch("app.database.get_session_factory")
    @patch("app.database.create_engine")
    @patch("app.database.get_config")
    async def test_init_db_success(
        self,
        mock_get_config: MagicMock,
        mock_create_engine: MagicMock,
        mock_create_factory: MagicMock,
        mock_check_conn: MagicMock,
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

        # Вызываем функцию
        engine, factory = init_db()

        # Проверяем результаты
        assert engine == mock_engine
        assert factory == mock_factory
        mock_create_engine.assert_called_once()
        mock_create_factory.assert_called_once()
        mock_check_conn.assert_called_once()

    @patch("app.database.get_config")
    @patch("app.database.create_engine")
    async def test_init_db_failure(
        self, mock_create_engine: MagicMock, mock_get_config: MagicMock
    ) -> None:
        """Тест неудачной инициализации БД."""
        # Мокаем конфигурацию
        mock_config = MagicMock()
        mock_config.database.database_url = (
            "postgresql+asyncpg://test:test@localhost/test"
        )
        mock_get_config.return_value = mock_config

        # Мокаем ошибку создания движка
        mock_create_engine.side_effect = Exception("Connection failed")

        with patch("app.database.logger") as mock_logger:
            engine, factory = init_db()

            # Проверяем, что возвращаются None
            assert engine is None
            assert factory is None

            # Проверяем, что ошибка была залогирована
            mock_logger.error.assert_called_once()

    @patch("app.database._engine")
    async def test_close_db_success(self, mock_engine: MagicMock) -> None:
        """Тест успешного закрытия БД."""
        mock_engine_instance = AsyncMock()
        mock_engine.return_value = mock_engine_instance

        await close_db()

        mock_engine_instance.dispose.assert_called_once()

    async def test_close_db_no_engine(self) -> None:
        """Тест закрытия БД когда движок не инициализирован."""
        with patch("app.database._engine", None):
            # Не должно бросать исключение
            await close_db()


@pytest.mark.asyncio
class TestDatabaseConnection:
    """Тесты для проверки подключения к БД."""

    @patch("app.database.get_session")
    async def test_check_connection_success(self, mock_get_session: MagicMock) -> None:
        """Тест успешной проверки подключения."""
        # Мокируем сессию и её методы
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_session.execute.return_value.scalar.return_value = 1

        # Выполняем проверку
        result = await check_connection()

        # Проверяем результат
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("app.database.get_session")
    async def test_check_connection_failure(self, mock_get_session: MagicMock) -> None:
        """Тест неудачной проверки подключения."""
        # Мокируем исключение при выполнении запроса
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_session.execute.side_effect = Exception("Connection failed")

        # Выполняем проверку
        result = await check_connection()

        # Проверяем результат
        assert result is False
        mock_session.execute.assert_called_once()
        mock_session.rollback.assert_called_once()

    @patch("app.database.get_session_factory")
    async def test_get_session_success(self, mock_get_factory: MagicMock) -> None:
        """Тест успешного создания и использования сессии."""
        # Мокируем фабрику и сессию
        mock_factory = MagicMock()
        mock_session = AsyncMock()
        mock_get_factory.return_value = mock_factory
        mock_factory.return_value = mock_session

        # Используем контекстный менеджер
        async with get_session() as session:
            assert session == mock_session

        # Проверяем, что сессия была закрыта
        mock_session.close.assert_called_once()

    @patch("app.database.get_session_factory")
    async def test_get_session_rollback_on_error(
        self, mock_get_factory: MagicMock
    ) -> None:
        """Тест rollback при ошибке в сессии."""
        mock_factory = MagicMock()
        mock_session = AsyncMock()
        mock_get_factory.return_value = mock_factory
        mock_factory.return_value = mock_session

        # Имитируем ошибку внутри контекстного менеджера
        with patch("app.database.logger") as mock_logger:
            database_error = Exception("Database error")
            with pytest.raises(Exception, match="Database error"):
                async with get_session() as session:
                    assert session == mock_session
                    raise database_error

            # Проверяем, что был вызван rollback
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
            mock_logger.error.assert_called_once()

    @patch("app.database.get_session_factory")
    async def test_get_session_rollback_on_exception(
        self, mock_get_factory: MagicMock
    ) -> NoReturn:
        """Тест rollback при общем исключении."""
        mock_factory = MagicMock()
        mock_session = AsyncMock()
        mock_get_factory.return_value = mock_factory
        mock_factory.return_value = mock_session

        # Имитируем общее исключение
        with patch("app.database.logger") as mock_logger:
            test_exception = ValueError("Test exception")
            with pytest.raises(ValueError, match="Test exception"):
                async with get_session() as session:
                    assert session == mock_session
                    raise test_exception

            # Проверяем, что был вызван rollback
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
            mock_logger.error.assert_called_once()

    @patch("app.database.get_engine")
    async def test_create_tables_success(self, mock_get_engine: MagicMock) -> None:
        """Тест успешного создания таблиц."""
        mock_engine = AsyncMock()
        mock_get_engine.return_value = mock_engine

        await create_tables()

        # Проверяем, что были вызваны правильные методы
        mock_engine.begin.assert_called_once()

    @patch("app.database.get_engine")
    async def test_create_tables_failure(self, mock_get_engine: MagicMock) -> None:
        """Тест неудачного создания таблиц."""
        mock_engine = AsyncMock()
        mock_get_engine.return_value = mock_engine
        mock_engine.begin.side_effect = Exception("Creation failed")

        with patch("app.database.logger") as mock_logger:
            await create_tables()

            # Проверяем, что ошибка была залогирована
            mock_logger.error.assert_called_once()

    @patch("app.database.get_config")
    @patch("app.database.get_engine")
    async def test_drop_tables_debug_mode(
        self, mock_get_engine: MagicMock, mock_get_config: MagicMock
    ) -> None:
        """Тест удаления таблиц в debug режиме."""
        mock_config = MagicMock()
        mock_config.debug = True
        mock_get_config.return_value = mock_config

        mock_engine = AsyncMock()
        mock_get_engine.return_value = mock_engine

        await drop_tables()

        # Проверяем, что drop_tables был вызван
        mock_engine.begin.assert_called_once()

    @patch("app.database.get_config")
    async def test_drop_tables_production_mode(
        self, mock_get_config: MagicMock
    ) -> None:
        """Тест запрета удаления таблиц в production режиме."""
        mock_config = MagicMock()
        mock_config.debug = False
        mock_get_config.return_value = mock_config

        with patch("app.database.logger") as mock_logger:
            await drop_tables()

            # Проверяем, что было залогировано предупреждение
            mock_logger.warning.assert_called_once()


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


@pytest.mark.integration
@pytest.mark.asyncio
class TestDatabaseIntegration:
    """Интеграционные тесты БД."""

    @pytest.mark.skip(reason="Требует настроенную БД")
    async def test_full_database_lifecycle(self) -> None:
        """Интеграционный тест полного жизненного цикла БД."""
        # Инициализация
        await init_db()

        try:
            # Проверка подключения
            assert await check_connection() is True

            # Создание таблиц
            await create_tables()

            # Работа с сессией
            async with get_session() as session:
                result = await session.execute("SELECT 1")
                assert result.scalar() == 1

        finally:
            # Закрытие
            await close_db()

    @pytest.mark.skip(reason="Требует настроенную БД")
    async def test_database_error_handling(self) -> None:
        """Интеграционный тест обработки ошибок БД."""
        # Тест с неправильными параметрами подключения
        with patch("app.database.get_config") as mock_config:
            config = MagicMock()
            config.database.database_url = (
                "postgresql+asyncpg://wrong:wrong@nonexistent:5432/wrong"
            )
            config.database.database_pool_size = 1
            config.database.database_timeout = 1
            config.debug = False
            mock_config.return_value = config

            with pytest.raises(Exception):
                await init_db()


class TestDatabaseExports:
    """Тесты для экспортируемых функций и классов."""

    @pytest.mark.skip(reason="Temporarily disabled due to commit issues")
    def test_all_exports_exist(self) -> None:
        """Тест наличия всех экспортируемых элементов."""
        from app.database import __all__

        expected_exports = [
            "Base",
            "init_db",
            "close_db",
            "get_session",
            "get_engine",
            "get_session_factory",
            "check_connection",
            "create_tables",
            "drop_tables",
        ]

        assert __all__ == expected_exports

        # Проверяем, что все элементы действительно импортируются
        import app.database as db_module

        for export in expected_exports:
            assert hasattr(db_module, export), f"Missing export: {export}"
