"""
@file: gettext.py
@description: Функции для получения текста из лексиконов
@created: 2025-10-07
"""

from typing import Any

from app.lexicon.en import LEXICON_EN
from app.lexicon.ru import LEXICON_RU
from app.log_lexicon.en import LOG_LEXICON_EN
from app.log_lexicon.ru import LOG_LEXICON_RU

# Словари лексиконов
LEXICONS = {"ru": LEXICON_RU, "en": LEXICON_EN}

LOG_LEXICONS = {"ru": LOG_LEXICON_RU, "en": LOG_LEXICON_EN}


def get_text(key: str, lang_code: str = "ru", **kwargs: Any) -> str:
    """
    Получение текста из лексикона по ключу.

    Args:
        key: Ключ в формате "section.subsection.key"
        lang_code: Код языка (по умолчанию "ru")
        **kwargs: Параметры для форматирования строки

    Returns:
        Отформатированная строка из лексикона или заглушка при отсутствии ключа
    """
    try:
        parts = key.split(".")
        current_dict = LEXICONS.get(lang_code, LEXICON_RU)  # Default to Russian

        # Проходим по частям ключа для навигации по вложенным словарям
        for part in parts:
            current_dict = current_dict[part]

        # Форматируем строку если есть параметры
        return current_dict.format(**kwargs) if kwargs else current_dict
    except (KeyError, AttributeError, TypeError):
        # Возвращаем заглушку для отсутствующих ключей
        return f"‼MISSING_TEXT: {key} (lang={lang_code})"


def get_log_text(key: str, lang_code: str = "ru", **kwargs: Any) -> str:
    """
    Получение текста для логирования из лог-лексикона по ключу.

    Args:
        key: Ключ в формате "section.subsection.key"
        lang_code: Код языка (по умолчанию "ru")
        **kwargs: Параметры для форматирования строки

    Returns:
        Отформатированная строка из лог-лексикона или заглушка при отсутствии ключа
    """
    try:
        parts = key.split(".")
        current_dict = LOG_LEXICONS.get(lang_code, LOG_LEXICON_RU)  # Default to Russian

        # Проходим по частям ключа для навигации по вложенным словарям
        for part in parts:
            current_dict = current_dict[part]

        # Форматируем строку если есть параметры
        return current_dict.format(**kwargs) if kwargs else current_dict
    except (KeyError, AttributeError, TypeError):
        # Возвращаем заглушку для отсутствующих ключей
        return f"‼MISSING_LOG_TEXT: {key} (lang={lang_code})"
