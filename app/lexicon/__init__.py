"""
@file: lexicon/__init__.py
@description: Инициализация модуля лексиконов
@created: 2025-10-03
"""

# Импортируем основные лексиконы для обратной совместимости
from . import ai_providers, callbacks, keyboards, message, start, utils

# Явно экспортируем модули
__all__ = ['ai_providers', 'callbacks', 'keyboards', 'message', 'start', 'utils']