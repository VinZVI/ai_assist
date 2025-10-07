"""
@file: log_lexicon/__init__.py
@description: Инициализация модуля лог-лексиконов
@created: 2025-10-03
@updated: 2025-10-07
"""

from app.lexicon.gettext import get_log_text

from .en import LOG_LEXICON_EN
from .ru import LOG_LEXICON_RU

# Для обратной совместимости по умолчанию используем русский лог-лексикон
LOG_LEXICON = LOG_LEXICON_RU

# Явно экспортируем модули
__all__ = ["LOG_LEXICON", "LOG_LEXICON_EN", "LOG_LEXICON_RU", "get_log_text"]
