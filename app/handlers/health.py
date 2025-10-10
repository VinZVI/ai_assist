"""
@file: handlers/health.py
@description: Обработчик для healthcheck endpoint
@dependencies: aiogram, loguru
@created: 2025-10-05
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

# Создаем роутер для обработчиков healthcheck
health_router = Router(name="health")


@health_router.message(Command("health"))
async def health_check(message: Message) -> None:
    """
    Healthcheck endpoint для проверки состояния приложения.

    Args:
        message: Объект сообщения от пользователя
    """
    try:
        # Отправляем простой ответ о состоянии здоровья
        await message.answer("✅ Приложение работает нормально")
        logger.info("Health check passed")

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        await message.answer(f"❌ Ошибка healthcheck: {e}")


# Экспорт роутера для регистрации в основном приложении
__all__ = ["health_router"]
