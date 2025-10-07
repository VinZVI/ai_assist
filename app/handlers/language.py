"""
@file: handlers/language.py
@description: Обработчик команды выбора языка
@dependencies: aiogram, sqlalchemy
@created: 2025-10-07
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from loguru import logger

from app.database import get_session
from app.lexicon.gettext import get_log_text, get_text
from app.models import User

# Создаем роутер для обработчиков команды выбора языка
language_router = Router(name="language")


@language_router.message(Command("language"))
async def handle_language_command(message: Message) -> None:
    """
    Обработчик команды /language.

    Показывает текущий язык пользователя и предлагает выбрать другой язык.

    Args:
        message: Объект сообщения от пользователя
    """
    # Проверяем, что у сообщения есть from_user
    if not message.from_user:
        logger.error("Получено сообщение без информации о пользователе")
        return

    try:
        # Получаем пользователя из базы данных
        async with get_session() as session:
            from sqlalchemy import select

            stmt = select(User).where(User.telegram_id == message.from_user.id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                await message.answer(get_text("errors.user_registration_error"))
                return

            # Получаем текущий язык пользователя
            current_language = user.language_code or "ru"

            # Создаем клавиатуру с выбором языков
            keyboard = create_language_keyboard(current_language)

            # Отправляем сообщение с выбором языка
            await message.answer(
                f"🌐 <b>{get_text('language.title', current_language)}</b>\n\n"
                f"{get_text('language.current_language', current_language, language=get_text('language.available_languages.' + current_language, current_language))}\n\n"
                f"{get_text('language.select_language', current_language)}",
                reply_markup=keyboard,
                parse_mode="HTML",
            )

            logger.info(
                get_log_text("language.language_command_processed").format(
                    user_id=message.from_user.id
                )
            )

    except Exception as e:
        logger.error(
            get_log_text("language.language_command_error").format(
                user_id=message.from_user.id, error=e
            )
        )
        await message.answer(get_text("errors.general_error"))


def create_language_keyboard(current_language: str) -> InlineKeyboardMarkup:
    """
    Создание клавиатуры для выбора языка.

    Args:
        current_language: Текущий язык пользователя

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками выбора языка
    """
    # Получаем доступные языки
    languages = {"ru": "🇷🇺 Русский", "en": "🇺🇸 English"}

    buttons = []
    for lang_code, lang_name in languages.items():
        # Добавляем эмодзи отметки для текущего языка
        button_text = f"✅ {lang_name}" if lang_code == current_language else lang_name

        buttons.append(
            [
                InlineKeyboardButton(
                    text=button_text, callback_data=f"select_language:{lang_code}"
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@language_router.callback_query(F.data.startswith("select_language:"))
async def handle_language_selection(callback: CallbackQuery) -> None:
    """
    Обработчик выбора языка через callback.

    Args:
        callback: Callback запрос от пользователя
    """
    # Проверяем, что у callback есть data и from_user
    if not callback.data or not callback.from_user:
        await callback.answer(get_text("errors.general_error"))
        return

    try:
        # Извлекаем код языка из callback данных
        lang_code = callback.data.split(":")[1]

        # Проверяем, что язык поддерживается
        supported_languages = ["ru", "en"]
        if lang_code not in supported_languages:
            await callback.answer(get_text("errors.general_error"))
            return

        # Проверяем, что у callback есть message и оно доступно
        if not callback.message:
            await callback.answer(get_text("errors.general_error"))
            return

        # Проверяем, что сообщение доступно для редактирования (не InaccessibleMessage)
        from aiogram.types import InaccessibleMessage

        if isinstance(callback.message, InaccessibleMessage):
            await callback.answer(get_text("errors.general_error"))
            return

        # Обновляем язык пользователя в базе данных
        async with get_session() as session:
            from sqlalchemy import select, update

            # Получаем пользователя
            stmt = select(User).where(User.telegram_id == callback.from_user.id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                await callback.answer(get_text("errors.user_registration_error"))
                return

            # Обновляем язык пользователя
            update_stmt = (
                update(User)
                .where(User.telegram_id == callback.from_user.id)
                .values(language_code=lang_code)
            )
            await session.execute(update_stmt)
            await session.commit()

            # Получаем название языка
            language_name = get_text(
                f"language.available_languages.{lang_code}", lang_code
            )

            # Отправляем подтверждение
            await callback.message.edit_text(
                f"✅ {get_text('language.language_changed', lang_code, language=language_name)}",
                parse_mode="HTML",
            )

            await callback.answer()

            logger.info(
                get_log_text("language.language_changed_success").format(
                    user_id=callback.from_user.id, language=lang_code
                )
            )

    except Exception as e:
        logger.error(
            get_log_text("language.language_selection_error").format(
                user_id=callback.from_user.id, error=e
            )
        )
        await callback.answer(get_text("errors.general_error"))
