#!/usr/bin/env python3
"""
@file: test_config_simple.py
@description: Простой тест системы конфигурации
@dependencies: app.config
@created: 2025-09-12
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger


def test_env_file():
    """Тестирование наличия и содержимого .env файла."""
    env_path = Path(".env")

    if not env_path.exists():
        logger.error("❌ Файл .env не найден!")
        return False

    logger.info("✅ Файл .env найден")

    # Читаем содержимое
    with open(env_path, encoding="utf-8") as f:
        content = f.read()

    # Проверяем ключевые переменные
    required_vars = [
        "BOT_TOKEN",
        "DATABASE_URL",
        "DEEPSEEK_API_KEY",
        "SECRET_KEY",
        "ADMIN_USER_ID",
    ]

    missing_vars = []
    for var in required_vars:
        if f"{var}=" not in content:
            missing_vars.append(var)
        else:
            logger.info(f"✅ Переменная {var} найдена")

    if missing_vars:
        logger.error(f"❌ Отсутствуют переменные: {missing_vars}")
        return False

    return True


def test_basic_config():
    """Тестирование базовой загрузки конфигурации."""
    try:
        from app.config import DatabaseConfig, TelegramConfig

        # Тестируем DatabaseConfig
        logger.info("🔧 Тестирование DatabaseConfig...")
        db_config = DatabaseConfig()
        logger.info(f"✅ Database URL: {db_config.database_url}")

        # Тестируем TelegramConfig
        logger.info("🔧 Тестирование TelegramConfig...")
        tg_config = TelegramConfig()
        logger.info(f"✅ Bot token: {tg_config.bot_token[:10]}...")

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка загрузки конфигурации: {e}")
        return False


def main():
    """Главная функция тестирования."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level="INFO",
    )

    logger.info("🔧 Простое тестирование конфигурации")
    logger.info("-" * 40)

    # Тест 1: Проверка .env файла
    logger.info("🔬 Тест 1: Проверка .env файла")
    env_ok = test_env_file()

    if not env_ok:
        logger.error("💔 Тест .env файла провален")
        return

    # Тест 2: Загрузка конфигурации
    logger.info("\n🔬 Тест 2: Загрузка конфигурации")
    config_ok = test_basic_config()

    if config_ok:
        logger.success("🎉 Все тесты пройдены!")
    else:
        logger.error("💔 Тест конфигурации провален")


if __name__ == "__main__":
    main()
