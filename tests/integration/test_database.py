"""
@file: test_database.py
@description: Тесты для модуля database.py и работы с базой данных
@dependencies: pytest, pytest-asyncio, sqlalchemy
@created: 2025-09-12
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.database import (
    create_engine,
    create_session_factory,
    init_db,
    close_db,
    check_connection,
    get_engine,
    get_session_factory,
    get_session,
    create_tables,
    drop_tables,
    Base
)


@pytest.mark.asyncio
class TestDatabaseEngine:
    """Тесты для создания и управления движком БД."""
    
    @patch('app.database.get_config')
    @patch('app.database.create_async_engine')
    async def test_create_engine_success(self, mock_create_async_engine, mock_get_config):
        """Тест успешного создания движка БД."""
        # Мокируем конфигурацию
        mock_config = MagicMock()
        mock_config.database.database_url = "postgresql+asyncpg://user:pass@localhost:5432/testdb"
        mock_config.database.database_pool_size = 10
        mock_config.database.database_timeout = 30
        mock_config.debug = False
        mock_get_config.return_value = mock_config
        
        # Мокируем создание движка
        mock_engine = MagicMock(spec=AsyncEngine)
        mock_create_async_engine.return_value = mock_engine
        
        engine = create_engine()
        
        # Проверяем, что движок создался
        assert engine == mock_engine
        
        # Проверяем, что create_async_engine вызван с правильными параметрами
        mock_create_async_engine.assert_called_once()
        call_args = mock_create_async_engine.call_args
        
        # Проверяем URL
        assert call_args[0][0] == "postgresql+asyncpg://user:pass@localhost:5432/testdb"
        
        # Проверяем параметры пула
        assert call_args[1]['pool_size'] == 10
        assert call_args[1]['pool_timeout'] == 30
        assert call_args[1]['pool_recycle'] == 3600
        assert call_args[1]['pool_pre_ping'] is True
    
    @patch('app.database.get_config')
    async def test_create_engine_debug_mode(self, mock_get_config):
        """Тест создания движка в debug режиме."""
        mock_config = MagicMock()
        mock_config.database.database_url = "postgresql+asyncpg://localhost/testdb"
        mock_config.database.database_pool_size = 5
        mock_config.database.database_timeout = 15
        mock_config.debug = True
        mock_get_config.return_value = mock_config
        
        with patch('app.database.create_async_engine') as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine
            
            create_engine()
            
            # В debug режиме должен быть echo=True
            call_args = mock_create.call_args[1]
            assert call_args['echo'] is True
            assert call_args['echo_pool'] is True
    
    async def test_create_session_factory(self):
        """Тест создания фабрики сессий."""
        mock_engine = MagicMock(spec=AsyncEngine)
        
        with patch('app.database.async_sessionmaker') as mock_sessionmaker:
            mock_factory = MagicMock()
            mock_sessionmaker.return_value = mock_factory
            
            factory = create_session_factory(mock_engine)
            
            assert factory == mock_factory
            mock_sessionmaker.assert_called_once_with(
                mock_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )


@pytest.mark.asyncio
class TestDatabaseInitialization:
    """Тесты для инициализации и закрытия БД."""
    
    @patch('app.database.create_engine')
    @patch('app.database.create_session_factory')
    @patch('app.database.check_connection')
    async def test_init_db_success(self, mock_check_conn, mock_create_factory, mock_create_engine):
        """Тест успешной инициализации БД."""
        mock_engine = MagicMock()
        mock_factory = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_create_factory.return_value = mock_factory
        mock_check_conn.return_value = True
        
        await init_db()
        
        mock_create_engine.assert_called_once()
        mock_create_factory.assert_called_once_with(mock_engine)
        mock_check_conn.assert_called_once()
    
    @patch('app.database.create_engine')
    async def test_init_db_failure(self, mock_create_engine):
        """Тест неудачной инициализации БД."""
        mock_create_engine.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception, match="Database connection failed"):
            await init_db()
    
    @patch('app.database._engine')
    async def test_close_db_success(self, mock_engine):
        """Тест успешного закрытия БД."""
        mock_engine_instance = AsyncMock()
        mock_engine = mock_engine_instance
        
        with patch('app.database._engine', mock_engine_instance):
            await close_db()
            
            mock_engine_instance.dispose.assert_called_once()
    
    async def test_close_db_no_engine(self):
        """Тест закрытия БД когда движок не инициализирован."""
        with patch('app.database._engine', None):
            # Не должно бросать исключение
            await close_db()


@pytest.mark.asyncio
class TestDatabaseConnection:
    """Тесты для проверки подключения к БД."""
    
    @patch('app.database.get_session')
    async def test_check_connection_success(self, mock_get_session):
        """Тест успешной проверки подключения."""
        # Мокируем сессию и её методы
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result
        
        # Мокируем контекстный менеджер
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = None
        
        result = await check_connection()
        
        assert result is True
        mock_session.execute.assert_called_once()
    
    @patch('app.database.get_session')
    async def test_check_connection_failure(self, mock_get_session):
        """Тест неудачной проверки подключения."""
        # Мокируем исключение при выполнении запроса
        mock_session = AsyncMock()
        mock_session.execute.side_effect = SQLAlchemyError("Connection failed")
        
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = None
        
        result = await check_connection()
        
        assert result is False


@pytest.mark.asyncio 
class TestDatabaseGetters:
    """Тесты для getter функций БД."""
    
    def test_get_engine_success(self):
        """Тест получения движка когда он инициализирован."""
        mock_engine = MagicMock()
        
        with patch('app.database._engine', mock_engine):
            engine = get_engine()
            assert engine == mock_engine
    
    def test_get_engine_not_initialized(self):
        """Тест получения движка когда он не инициализирован."""
        with patch('app.database._engine', None):
            with pytest.raises(RuntimeError, match="База данных не инициализирована"):
                get_engine()
    
    def test_get_session_factory_success(self):
        """Тест получения фабрики сессий когда она инициализирована."""
        mock_factory = MagicMock()
        
        with patch('app.database._session_factory', mock_factory):
            factory = get_session_factory()
            assert factory == mock_factory
    
    def test_get_session_factory_not_initialized(self):
        """Тест получения фабрики сессий когда она не инициализирована."""
        with patch('app.database._session_factory', None):
            with pytest.raises(RuntimeError, match="База данных не инициализирована"):
                get_session_factory()


@pytest.mark.asyncio
class TestDatabaseSession:
    """Тесты для работы с сессиями БД."""
    
    @patch('app.database.get_session_factory')
    async def test_get_session_success(self, mock_get_factory):
        """Тест успешного создания и использования сессии."""
        # Мокируем фабрику и сессию
        mock_session = AsyncMock()
        mock_factory = MagicMock()
        mock_factory.return_value = mock_session
        mock_get_factory.return_value = mock_factory
        
        # Тестируем контекстный менеджер
        async with get_session() as session:
            assert session == mock_session
        
        # Проверяем, что методы были вызваны
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
    
    @patch('app.database.get_session_factory')
    async def test_get_session_rollback_on_error(self, mock_get_factory):
        """Тест rollback при ошибке в сессии."""
        mock_session = AsyncMock()
        mock_factory = MagicMock()
        mock_factory.return_value = mock_session
        mock_get_factory.return_value = mock_factory
        
        # Мокируем ошибку в работе сессии
        mock_session.commit.side_effect = SQLAlchemyError("Commit failed")
        
        with pytest.raises(SQLAlchemyError):
            async with get_session() as session:
                pass  # Ошибка возникнет при commit
        
        # Проверяем, что был вызван rollback
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
    
    @patch('app.database.get_session_factory')
    async def test_get_session_rollback_on_exception(self, mock_get_factory):
        """Тест rollback при общем исключении."""
        mock_session = AsyncMock()
        mock_factory = MagicMock()
        mock_factory.return_value = mock_session
        mock_get_factory.return_value = mock_factory
        
        with pytest.raises(ValueError):
            async with get_session() as session:
                raise ValueError("Test exception")
        
        # Проверяем, что был вызван rollback
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


@pytest.mark.asyncio
class TestDatabaseTables:
    """Тесты для создания и удаления таблиц."""
    
    @patch('app.database.get_engine')
    async def test_create_tables_success(self, mock_get_engine):
        """Тест успешного создания таблиц."""
        mock_engine = AsyncMock()
        mock_connection = AsyncMock()
        mock_get_engine.return_value = mock_engine
        
        # Мокируем контекстный менеджер begin
        mock_engine.begin.return_value.__aenter__.return_value = mock_connection
        mock_engine.begin.return_value.__aexit__.return_value = None
        
        await create_tables()
        
        mock_engine.begin.assert_called_once()
        mock_connection.run_sync.assert_called_once()
    
    @patch('app.database.get_engine')
    async def test_create_tables_failure(self, mock_get_engine):
        """Тест неудачного создания таблиц."""
        mock_engine = AsyncMock()
        mock_engine.begin.side_effect = Exception("Table creation failed")
        mock_get_engine.return_value = mock_engine
        
        with pytest.raises(Exception, match="Table creation failed"):
            await create_tables()
    
    @patch('app.database.get_config')
    @patch('app.database.get_engine')
    async def test_drop_tables_debug_mode(self, mock_get_engine, mock_get_config):
        """Тест удаления таблиц в debug режиме."""
        mock_config = MagicMock()
        mock_config.debug = True
        mock_get_config.return_value = mock_config
        
        mock_engine = AsyncMock()
        mock_connection = AsyncMock()
        mock_get_engine.return_value = mock_engine
        
        mock_engine.begin.return_value.__aenter__.return_value = mock_connection
        mock_engine.begin.return_value.__aexit__.return_value = None
        
        await drop_tables()
        
        mock_engine.begin.assert_called_once()
        mock_connection.run_sync.assert_called_once()
    
    @patch('app.database.get_config')
    async def test_drop_tables_production_mode(self, mock_get_config):
        """Тест запрета удаления таблиц в production режиме."""
        mock_config = MagicMock()
        mock_config.debug = False
        mock_get_config.return_value = mock_config
        
        with pytest.raises(RuntimeError, match="Удаление таблиц разрешено только в debug режиме"):
            await drop_tables()


@pytest.mark.asyncio
class TestDatabaseBase:
    """Тесты для базового класса моделей."""
    
    def test_base_exists(self):
        """Тест существования базового класса."""
        assert Base is not None
        
        # Проверяем, что это декларативная база SQLAlchemy
        assert hasattr(Base, 'metadata')
        assert hasattr(Base, 'registry')


@pytest.mark.integration
@pytest.mark.asyncio
class TestDatabaseIntegration:
    """Интеграционные тесты БД."""
    
    @pytest.mark.skip(reason="Требует настроенную БД")
    async def test_full_database_lifecycle(self):
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
    async def test_database_error_handling(self):
        """Интеграционный тест обработки ошибок БД."""
        # Тест с неправильными параметрами подключения
        with patch('app.database.get_config') as mock_config:
            config = MagicMock()
            config.database.database_url = "postgresql+asyncpg://wrong:wrong@nonexistent:5432/wrong"
            config.database.database_pool_size = 1
            config.database.database_timeout = 1
            config.debug = False
            mock_config.return_value = config
            
            with pytest.raises(Exception):
                await init_db()


class TestDatabaseExports:
    """Тесты для экспортируемых функций и классов."""
    
    def test_all_exports_exist(self):
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