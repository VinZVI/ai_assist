"""
@file: keyboards/inline.py
@description: Inline клавиатуры для Telegram бота
@dependencies: aiogram
@created: 2025-09-14
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Создание основного меню бота."""
    builder = InlineKeyboardBuilder()
    
    # Кнопки основного меню
    builder.row(
        InlineKeyboardButton(text="💬 Начать диалог", callback_data="start_chat"),
        InlineKeyboardButton(text="📊 Моя статистика", callback_data="my_stats"),
    )
    
    builder.row(
        InlineKeyboardButton(text="💎 Премиум доступ", callback_data="premium_info"),
        InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"),
    )
    
    builder.row(
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
    )
    
    return builder.as_markup()


def create_premium_keyboard(premium_price: int = 99) -> InlineKeyboardMarkup:
    """Создание клавиатуры для премиум функций."""
    builder = InlineKeyboardBuilder()
    
    # Информация о премиум
    builder.row(
        InlineKeyboardButton(
            text=f"💳 Купить премиум за {premium_price}₽", 
            callback_data=f"buy_premium:{premium_price}"
        ),
    )
    
    builder.row(
        InlineKeyboardButton(text="📜 Что даёт премиум?", callback_data="premium_features"),
        InlineKeyboardButton(text="❓ Часто задаваемые вопросы", callback_data="premium_faq"),
    )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu"),
    )
    
    return builder.as_markup()


def create_premium_features_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для показа функций премиума."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="💳 Купить премиум", callback_data="premium_info"),
    )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="premium_info"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"),
    )
    
    return builder.as_markup()


def create_stats_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для статистики пользователя."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📈 Детальная статистика", callback_data="detailed_stats"),
        InlineKeyboardButton(text="🏆 Мои достижения", callback_data="achievements"),
    )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"),
    )
    
    return builder.as_markup()


def create_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🌍 Язык", callback_data="settings_language"),
        InlineKeyboardButton(text="🔔 Уведомления", callback_data="settings_notifications"),
    )
    
    builder.row(
        InlineKeyboardButton(text="🗑️ Удалить данные", callback_data="settings_delete_data"),
    )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"),
    )
    
    return builder.as_markup()


def create_language_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en"),
    )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Настройки", callback_data="settings"),
    )
    
    return builder.as_markup()


def create_help_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура помощи."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📚 Руководство", callback_data="help_guide"),
        InlineKeyboardButton(text="❓ FAQ", callback_data="help_faq"),
    )
    
    builder.row(
        InlineKeyboardButton(text="📞 Поддержка", callback_data="help_support"),
        InlineKeyboardButton(text="🐛 Сообщить об ошибке", callback_data="help_bug_report"),
    )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"),
    )
    
    return builder.as_markup()


def create_confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}"),
        InlineKeyboardButton(text="❌ Нет", callback_data=f"cancel_{action}"),
    )
    
    return builder.as_markup()


def create_payment_keyboard(premium_price: int) -> InlineKeyboardMarkup:
    """Клавиатура для оплаты премиума."""
    builder = InlineKeyboardBuilder()
    
    # Кнопка оплаты через Telegram Stars
    builder.row(
        InlineKeyboardButton(
            text=f"⭐ Оплатить {premium_price} Telegram Stars",
            callback_data=f"pay_stars:{premium_price}"
        ),
    )
    
    # Альтернативные способы оплаты (если есть)
    builder.row(
        InlineKeyboardButton(text="💳 Другие способы оплаты", callback_data="other_payment_methods"),
    )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="premium_info"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu"),
    )
    
    return builder.as_markup()


def create_back_button(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
    """Простая кнопка Назад."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data),
    )
    
    return builder.as_markup()


# Экспорт всех функций
__all__ = [
    "create_main_menu_keyboard",
    "create_premium_keyboard",
    "create_premium_features_keyboard",
    "create_stats_keyboard",
    "create_settings_keyboard",
    "create_language_keyboard",
    "create_help_keyboard",
    "create_confirmation_keyboard",
    "create_payment_keyboard",
    "create_back_button",
]