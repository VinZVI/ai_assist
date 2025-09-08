"""
@file: tests/conftest.py
@description: Конфигурация pytest для тестов
@dependencies: pytest, pytest-asyncio
@created: 2025-09-07
"""

import sys
import pytest
from pathlib import Path

# Добавляем корневую папку проекта в Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """Фикстура возвращающая путь к корню проекта."""
    return project_root


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Автоматическая настройка тестового окружения."""
    # Настройка логирования для тестов
    from app.utils.logging import setup_logging
    
    setup_logging(
        log_level="WARNING",  # Только важные сообщения в тестах
        enable_console=False,  # Отключаем консольный вывод в тестах
        enable_json=False,
        log_file_path=None
    )


@pytest.fixture
def clean_config_cache():
    """Фикстура для очистки кеша конфигурации между тестами."""
    import app.config
    
    # Сохраняем текущее состояние
    original_instance = getattr(app.config, '_config_instance', None)
    
    # Очищаем кеш
    app.config._config_instance = None
    
    yield
    
    # Восстанавливаем состояние
    app.config._config_instance = original_instance


# Маркеры для категоризации тестов
def pytest_configure(config):
    """Конфигурация pytest с пользовательскими маркерами."""
    config.addinivalue_line(
        "markers", "unit: Юнит-тесты отдельных компонентов"
    )
    config.addinivalue_line(
        "markers", "integration: Интеграционные тесты"
    )
    config.addinivalue_line(
        "markers", "config: Тесты конфигурации"
    )
    config.addinivalue_line(
        "markers", "database: Тесты базы данных"
    )
    config.addinivalue_line(
        "markers", "telegram: Тесты Telegram интеграции"
    )
    config.addinivalue_line(
        "markers", "slow: Медленные тесты"
    )