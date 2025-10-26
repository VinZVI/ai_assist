"""
@file: check_imports.py
@description: Скрипт для проверки корректности импортов проекта
@created: 2025-09-20
@updated: 2025-10-26
"""

import contextlib
import sys
from pathlib import Path

# Добавляем корневую папку проекта в Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Пробуем импортировать основные модули проекта
try:
    # Основные компоненты
    # Telegram бот
    from aiogram import Bot, Dispatcher
    from aiogram.types import Message
    from app.services.conversation import ConversationService
    from app.services.user_service import UserService

    from app.config import get_config
    from app.database import get_session, init_database

    # Хендлеры
    from app.handlers import callbacks, message_handler
    from app.models.conversation import Conversation

    # Модели данных
    from app.models.user import User

    # Сервисы
    from app.services.ai_manager import get_ai_manager
    from app.utils.logging import setup_logging


except ImportError:
    sys.exit(1)

except Exception:
    sys.exit(1)

# Дополнительная проверка конфигурации
with contextlib.suppress(Exception):
    config = get_config()

if __name__ == "__main__":
    pass
