"""
@file: tests/conftest.py
@description: Конфигурация pytest для тестов
@dependencies: pytest, pytest-asyncio
@created: 2025-09-07
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import Chat, Message
from aiogram.types import User as TelegramUser

from app.config import AppConfig
from app.models.conversation import Conversation
from app.models.user import User
from app.services.ai_providers.base import AIResponse, ConversationMessage

# Импорты для фикстур (перемещены на верхний уровень)
from app.utils.logging import setup_logging

# Добавляем корневую папку проекта в Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path() -> Path:
    """Фикстура возвращающая путь к корню проекта."""
    return project_root


@pytest.fixture(autouse=True)
def setup_test_environment() -> None:
    """Автоматическая настройка тестового окружения."""
    # Настройка логирования для тестов
    setup_logging(
        log_level="WARNING",  # Только важные сообщения в тестах
        enable_console=False,  # Отключаем консольный вывод в тестах
        enable_json=False,
        log_file_path=None,
    )


@pytest.fixture
def clean_config_cache() -> None:
    """Фикстура для очистки кеша конфигурации между тестами."""
    # Сохраняем текущее состояние
    from app.config import _config

    # Сохраняем оригинальное значение
    original_config = _config

    # Очищаем кеш
    from app.config import _config

    _config = None

    # Восстанавливаем состояние после теста
    yield

    # Восстанавливаем оригинальное значение
    from app.config import _config

    _config = original_config


# =============================================================================
# Фикстуры для новой AI архитектуры
# =============================================================================


@pytest.fixture
def mock_config() -> AppConfig:
    """Мок конфигурации для тестов."""
    config = MagicMock()

    # DeepSeek конфигурация
    config.deepseek.deepseek_api_key = "test-deepseek-key"
    config.deepseek.deepseek_base_url = "https://api.deepseek.com"
    config.deepseek.deepseek_model = "deepseek-chat"
    config.deepseek.deepseek_temperature = 0.7
    config.deepseek.deepseek_max_tokens = 1000

    # OpenRouter конфигурация
    config.openrouter.openrouter_api_key = "test-openrouter-key"
    config.openrouter.openrouter_base_url = "https://openrouter.ai/api/v1"
    config.openrouter.openrouter_model = "anthropic/claude-3-haiku"
    config.openrouter.openrouter_site_url = "http://localhost"
    config.openrouter.openrouter_app_name = "AI-Assistant-Test"

    # AI провайдер настройки
    config.ai_provider.primary_provider = "openrouter"
    config.ai_provider.fallback_provider = "deepseek"
    config.ai_provider.enable_fallback = True
    config.ai_provider.max_retries_per_provider = 3

    return config


@pytest.fixture
def mock_ai_response() -> AIResponse:
    """Стандартный мок AI ответа."""

    return AIResponse(
        content="Это тестовый ответ от AI",
        model="test-model",
        provider="test-provider",
        tokens_used=25,
        response_time=0.5,
        cached=False,
    )


@pytest.fixture
def mock_conversation_messages() -> list[ConversationMessage]:
    """Тестовые сообщения диалога."""

    return [
        ConversationMessage(
            role="system",
            content="Ты полезный AI помощник.",
        ),
        ConversationMessage(
            role="user",
            content="Привет! Как дела?",
        ),
        ConversationMessage(
            role="assistant",
            content="Привет! У меня всё отлично, спасибо!",
        ),
    ]


@pytest.fixture
def mock_openrouter_provider() -> AsyncMock:
    """Мок OpenRouter провайдера."""
    provider = AsyncMock()
    provider.name = "openrouter"
    provider.is_configured.return_value = True
    provider.is_available.return_value = True
    return provider


@pytest.fixture
def mock_deepseek_provider() -> AsyncMock:
    """Мок DeepSeek провайдера."""
    provider = AsyncMock()
    provider.name = "deepseek"
    provider.is_configured.return_value = True
    provider.is_available.return_value = True
    return provider


@pytest.fixture
def mock_ai_manager(
    mock_openrouter_provider: AsyncMock,
    mock_deepseek_provider: AsyncMock,
    mock_ai_response: AIResponse,
) -> AsyncMock:
    """Мок AI менеджера с настроенными провайдерами."""
    manager = AsyncMock()

    # Настройка провайдеров
    manager.get_provider.side_effect = lambda name: {
        "openrouter": mock_openrouter_provider,
        "deepseek": mock_deepseek_provider,
    }.get(name)

    # Настройка асинхронных методов
    manager.generate_response.return_value = mock_ai_response
    manager.generate_simple_response.return_value = mock_ai_response
    manager.health_check.return_value = {
        "manager_status": "healthy",
        "providers": {
            "openrouter": {"status": "healthy"},
            "deepseek": {"status": "healthy"},
        },
    }

    # Настройка синхронных методов
    manager.get_stats = MagicMock(
        return_value={
            "requests_total": 100,
            "requests_successful": 95,
            "requests_failed": 5,
            "fallback_used": 2,
            "provider_stats": {
                "openrouter": {"requests": 60, "successes": 58},
                "deepseek": {"requests": 40, "successes": 37},
            },
        },
    )

    manager.clear_cache = MagicMock()

    return manager


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Мок сессии базы данных."""
    session = AsyncMock()
    session.get.return_value = None
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    return session
