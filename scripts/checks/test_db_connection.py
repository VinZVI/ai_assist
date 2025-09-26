#!/usr/bin/env python3
"""
@file: test_db_connection.py
@description: Тестовый скрипт для проверки подключения к базе данных
@dependencies: app.database, app.config
@created: 2025-09-12
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger

from app.config import get_config
from app.database import check_connection, close_db, init_db


async def test_database_connection() -> None:
    """Тестирование подключения к базе данных."""
    logger.info("🔧 Запуск теста подключения к базе данных...")

    try:
        # Загружаем конфигурацию
        config = get_config()
        logger.info("✅ Конфигурация загружена успешно")
        logger.info(
            f"📊 DATABASE_URL: {config.database.database_url.split('@')[1] if '@' in config.database.database_url else 'скрыт'}",
        )

        # Инициализируем базу данных
        await init_db()
        logger.info("✅ База данных инициализирована")

        # Проверяем подключение
        connection_ok = await check_connection()

        if connection_ok:
            logger.success("🎉 Подключение к базе данных работает отлично!")
        else:
            logger.error("❌ Подключение к базе данных не работает")
            return False

    except Exception as e:
        logger.error(f"💥 Ошибка при тестировании подключения: {e}")
        return False

    finally:
        # Закрываем подключение
        await close_db()
        logger.info("🔒 Подключение к базе данных закрыто")

    return True


async def test_models_import() -> None:
    """Тестирование импорта моделей."""
    logger.info("📦 Тестирование импорта моделей...")

    try:
        from app.models import Base, Conversation, User
        from app.models.conversation import ConversationCreate, MessageRole
        from app.models.user import UserCreate, UserResponse

        logger.info("✅ Все модели успешно импортированы")
        logger.info("📋 Доступные модели: User, Conversation")
        logger.info(f"🔧 Базовый класс: {Base}")
        logger.info("📝 Pydantic схемы: UserCreate, UserResponse, ConversationCreate")
        logger.info("🏷️ Enums: MessageRole")

    except ImportError as e:
        logger.error(f"❌ Ошибка импорта моделей: {e}")
        return False

    return True


async def main() -> None:
    """Главная функция тестирования."""
    logger.info("🚀 Начинаем комплексное тестирование базы данных")

    # Тест 1: Импорт моделей
    models_ok = await test_models_import()

    # Тест 2: Подключение к БД (только если модели загрузились)
    if models_ok:
        db_ok = await test_database_connection()

        if db_ok:
            logger.success("🎯 Все тесты пройдены успешно!")
            logger.info("✨ База данных готова к использованию")
        else:
            logger.error("💔 Тест подключения провален")
            sys.exit(1)
    else:
        logger.error("💔 Тест импорта моделей провален")
        sys.exit(1)


if __name__ == "__main__":
    # Настройка логирования для теста
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level="INFO",
    )

    # Запуск тестов
    asyncio.run(main())
