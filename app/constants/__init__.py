"""
@file: constants/__init__.py
@description: Инициализация модуля констант
@created: 2025-10-03
"""

# Импортируем основные классы констант для обратной совместимости
from .config import ConfigErrorMessages, ConfigMagicValues
from .errors import *  # noqa: F403

__all__ = ["ConfigErrorMessages", "ConfigMagicValues"]
