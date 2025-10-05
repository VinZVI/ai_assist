"""
@file: log_lexicon/__init__.py
@description: Инициализация модуля лог-лексиконов
@created: 2025-10-03
"""

# Импортируем лог-лексиконы для обратной совместимости
from . import (
    ai_providers,
    callbacks,
    config,
    database,
    keyboards,
    main,
    message,
    start,
    utils,
)

# Явно экспортируем модули
__all__ = [
    "ai_providers",
    "callbacks",
    "config",
    "database",
    "keyboards",
    "main",
    "message",
    "start",
    "utils",
]
