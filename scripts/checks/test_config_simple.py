#!/usr/bin/env python3
"""
Simple script to check if config is working properly
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger


def test_env_file() -> bool:
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
        "OPENROUTER_API_KEY",
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


def main() -> None:
    """Main function."""
    logger.info("🔍 Проверяем конфигурацию...")

    if test_env_file():
        logger.info("✅ Конфигурация в порядке!")
    else:
        logger.error("❌ Проблемы с конфигурацией!")


if __name__ == "__main__":
    main()
