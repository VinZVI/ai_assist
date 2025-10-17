"""
@file: lexicon/__init__.py
@description: Инициализация модуля лексиконов
@created: 2025-10-03
@updated: 2025-10-07
"""

# Импортируем новые централизованные лексиконы
from .en import LEXICON_EN
from .gettext import get_text
from .ru import LEXICON_RU

# Для обратной совместимости по умолчанию используем русский лексикон
LEXICON = LEXICON_RU

# Явно экспортируем модули
__all__ = ["LEXICON", "LEXICON_EN", "LEXICON_RU", "get_text"]
