"""
@file: scripts/diagnostics/test_lexicon_imports.py
@description: Диагностический скрипт для проверки импорта лексиконов
@created: 2025-10-03
"""

import sys
import warnings
from pathlib import Path
from typing import Optional

# Добавляем корневую директорию проекта в путь Python
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_lexicon_imports() -> bool | None:
    """Тест импорта лексиконов."""
    print("🔍 Проверка импорта лексиконов...")

    # Игнорируем предупреждения о устаревших модулях
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    try:
        # Тест импорта основных лексиконов
        from app.lexicon import callbacks, message, start

        print("✅ Основные лексиконы импортируются успешно")

        # Тест импорта новых лексиконов
        from app.lexicon import ai_providers, keyboards, utils

        print("✅ Новые лексиконы импортируются успешно")

        # Тест импорта лог-лексиконов (только новые модули)
        from app.log_lexicon import callbacks as log_callbacks
        from app.log_lexicon import message as log_message
        from app.log_lexicon import start as log_start

        print("✅ Основные лог-лексиконы импортируются успешно")

        # Тест импорта новых лог-лексиконов
        from app.log_lexicon import ai_providers as log_ai_providers
        from app.log_lexicon import keyboards as log_keyboards
        from app.log_lexicon import utils as log_utils

        print("✅ Новые лог-лексиконы импортируются успешно")

        # Тест импорта констант
        from app.constants import config, errors

        print("✅ Константы импортируются успешно")

        # Проверка доступности некоторых элементов
        print(f"✅ START_COMMAND_RECEIVED: {log_start.START_COMMAND_RECEIVED}")
        print(f"✅ MAIN_MENU_START_CHAT: {keyboards.MAIN_MENU_START_CHAT}")
        print(f"✅ AI_PROVIDER_INITIALIZING: {ai_providers.AI_PROVIDER_INITIALIZING}")
        print(f"✅ LOGGING_SYSTEM_INITIALIZED: {utils.LOGGING_SYSTEM_INITIALIZED}")

        print("🎉 Все лексиконы импортируются успешно!")
        return True

    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False


if __name__ == "__main__":
    success = test_lexicon_imports()
    sys.exit(0 if success else 1)
