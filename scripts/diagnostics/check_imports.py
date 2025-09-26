#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы импортов в IDE.
Если этот файл открыт в IDE и импорты подсвечиваются красным,
значит IDE не видит виртуальное окружение uv.
"""

import sys
from pathlib import Path

# Проверяем основные зависимости
try:
    import pytest

    print(f"✅ pytest {pytest.__version__} - OK")
except ImportError as e:
    print(f"❌ pytest не найден: {e}")

try:
    import loguru

    print(f"✅ loguru {loguru.__version__} - OK")
except ImportError as e:
    print(f"❌ loguru не найден: {e}")

try:
    import pydantic

    print(f"✅ pydantic {pydantic.__version__} - OK")
except ImportError as e:
    print(f"❌ pydantic не найден: {e}")

try:
    import aiogram

    print(f"✅ aiogram {aiogram.__version__} - OK")
except ImportError as e:
    print(f"❌ aiogram не найден: {e}")

# Проверяем путь к интерпретатору
print(f"\n📍 Python интерпретатор: {sys.executable}")
print(f"📁 Рабочая директория: {Path.cwd()}")
print(f"🐍 Версия Python: {sys.version}")

# Проверяем пути Python
print("\n📚 Python paths:")
for i, path in enumerate(sys.path[:5], 1):
    print(f"  {i}. {path}")

if __name__ == "__main__":
    print("\n🎉 Все импорты успешно загружены!")
    print("💡 Если в IDE все еще ошибки, настройте интерпретатор Python:")
    print("   VS Code: Ctrl+Shift+P -> 'Python: Select Interpreter'")
    print("   PyCharm: File -> Settings -> Project -> Python Interpreter")
    print(f"   Путь: {Path.cwd() / '.venv' / 'Scripts' / 'python.exe'}")
