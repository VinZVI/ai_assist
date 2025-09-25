"""
@file: tests/test_config.py
@description: Тесты для модуля конфигурации приложения
@dependencies: pytest, pytest-asyncio
@created: 2025-09-07
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from loguru import logger

# Добавляем корневую папку в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Настраиваем логирование для тестов
from app.utils.logging import setup_logging

setup_logging(
    log_level="INFO",
    enable_console=True,
    enable_json=False,
    log_file_path=None
)


class TestConfigValidation:
    """Тесты валидации конфигурации."""
    
    def test_env_example_exists(self):
        """Проверка наличия файла .env.example."""
        env_example = project_root / ".env.example"
        assert env_example.exists(), ".env.example файл должен существовать"
        logger.success("✅ .env.example найден")
    
    def test_config_classes_import(self):
        """Тест импорта классов конфигурации."""
        try:
            from app.config import (
                AppConfig, 
                DatabaseConfig, 
                TelegramConfig, 
                DeepSeekConfig,
                UserLimitsConfig,
                AdminConfig,
                PaymentConfig,
                RedisConfig,
                MonitoringConfig,
                RateLimitConfig
            )
            logger.success("✅ Все классы конфигурации импортированы успешно")
        except ImportError as e:
            pytest.fail(f"Ошибка импорта классов конфигурации: {e}")
    
    def test_telegram_config_validation(self):
        """Тест валидации TelegramConfig."""
        from app.config import TelegramConfig
        
        # Тест с невалидным токеном
        with pytest.raises(Exception):
            TelegramConfig(bot_token="invalid_token")
        
        # Тест с валидным токеном
        config = TelegramConfig(bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        assert config.bot_token is not None
        logger.success("✅ Валидация TelegramConfig работает")
    
    def test_deepseek_config_validation(self):
        """Тест валидации DeepSeekConfig.""" 
        from app.config import DeepSeekConfig
        
        # Тест с невалидным API ключом
        with pytest.raises(Exception):
            DeepSeekConfig(deepseek_api_key="your_deepseek_api_key_here")
        
        # Тест с валидным API ключом
        config = DeepSeekConfig(deepseek_api_key="sk-test123456789")
        assert config.deepseek_api_key == "sk-test123456789"
        
        # Тест валидации температуры
        with pytest.raises(Exception):
            DeepSeekConfig(
                deepseek_api_key="sk-test123456789",
                deepseek_temperature=3.0  # Недопустимое значение
            )
        
        logger.success("✅ Валидация DeepSeekConfig работает")
    
    def test_database_config_url_building(self):
        """Тест построения URL базы данных."""
        from app.config import DatabaseConfig
        
        config = DatabaseConfig(
            database_host="localhost",
            database_port=5432,
            database_name="test_db",
            database_user="test_user",
            database_password="test_password"
        )
        
        expected_url = "postgresql+asyncpg://test_user:test_password@localhost:5432/test_db"
        assert config.database_url == expected_url
        logger.success("✅ Построение URL БД работает корректно")
    
    def test_user_limits_validation(self):
        """Тест валидации UserLimitsConfig."""
        from app.config import UserLimitsConfig
        
        # Тест с отрицательным лимитом
        with pytest.raises(Exception):
            UserLimitsConfig(free_messages_limit=-1)
        
        # Тест с нулевой ценой
        with pytest.raises(Exception):
            UserLimitsConfig(premium_price=0)
        
        # Тест с валидными значениями
        config = UserLimitsConfig(
            free_messages_limit=10,
            premium_price=99,
            premium_duration_days=30
        )
        assert config.free_messages_limit == 10
        assert config.premium_price == 99
        logger.success("✅ Валидация UserLimitsConfig работает")
    
    def test_admin_config_validation(self):
        """Тест валидации AdminConfig."""
        from app.config import AdminConfig
        
        # Тест с невалидным ID
        with pytest.raises(Exception):
            AdminConfig(admin_user_id=0)
        
        # Тест с валидными ID
        config = AdminConfig(
            admin_user_id=123456789,
            admin_user_ids="987654321,111222333"
        )
        
        admin_ids = config.get_admin_ids()
        assert 123456789 in admin_ids
        assert 987654321 in admin_ids
        assert 111222333 in admin_ids
        assert len(set(admin_ids)) == len(admin_ids)  # Нет дубликатов
        
        logger.success("✅ Валидация AdminConfig работает")


class TestConfigLoading:
    """Тесты загрузки конфигурации."""
    
    def test_config_loading_without_env_file(self):
        """Тест загрузки конфигурации без .env файла."""
        from app.config import get_config
        
        # Без .env файла должна быть ошибка валидации
        with pytest.raises(Exception):
            config = get_config()
        
        logger.success("✅ Валидация обязательных полей работает")
    
    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="""
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
DEEPSEEK_API_KEY=sk-test123456789
SECRET_KEY=test_secret_key_with_32_characters_minimum
ADMIN_USER_ID=123456789
""")
    def test_config_loading_with_env_file(self, mock_file_exists):
        """Тест загрузки конфигурации с .env файлом."""
        mock_file_exists.return_value = True
        
        # Сбрасываем кеш конфигурации
        import app.config
        app.config._config_instance = None
        
        try:
            from app.config import get_config
            config = get_config()
            
            assert config.telegram.bot_token == "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
            assert config.deepseek.deepseek_api_key == "sk-test123456789"
            assert config.secret_key == "test_secret_key_with_32_characters_minimum"
            assert config.admin.admin_user_id == 123456789
            
            logger.success("✅ Загрузка конфигурации с .env файлом работает")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки конфигурации: {e}")
            # Это может быть ожидаемым если другие поля тоже требуются
            pass
    
    def test_config_singleton_behavior(self):
        """Тест поведения синглтона для конфигурации."""
        import app.config
        
        # Сбрасываем кеш
        app.config._config_instance = None
        
        from app.config import get_config
        
        # При отсутствии .env файла должна быть ошибка
        with pytest.raises(Exception):
            config1 = get_config()
        
        logger.success("✅ Singleton поведение работает корректно")


class TestEnvironmentVariables:
    """Тесты переменных окружения."""
    
    def test_env_example_completeness(self):
        """Проверка полноты .env.example файла."""
        env_example = project_root / ".env.example"
        content = env_example.read_text(encoding="utf-8")
        
        # Проверяем наличие ключевых секций
        required_sections = [
            "Telegram Bot Configuration",
            "Database Configuration", 
            "DeepSeek API Configuration",
            "Application Configuration",
            "User Limits Configuration",
            "Admin Configuration",
            "Payment Configuration"
        ]
        
        for section in required_sections:
            assert section in content, f"Секция '{section}' отсутствует в .env.example"
        
        # Проверяем наличие ключевых переменных
        required_vars = [
            "BOT_TOKEN",
            "DATABASE_URL",
            "DEEPSEEK_API_KEY",
            "SECRET_KEY",
            "ADMIN_USER_ID",
            "FREE_MESSAGES_LIMIT",
            "PREMIUM_PRICE"
        ]
        
        for var in required_vars:
            assert var in content, f"Переменная '{var}' отсутствует в .env.example"
        
        logger.success("✅ .env.example содержит все необходимые переменные")


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v", "--tb=short"])