"""
@file: handlers/health.py
@description: Обработчик для healthcheck endpoint
@dependencies: aiogram, loguru
@created: 2025-10-05
"""

from aiogram import Router
from aiogram.types import Message
from loguru import logger

from app.config import get_config
from app.database import get_session

# Создаем роутер для обработчиков healthcheck
health_router = Router(name="health")


@health_router.message(lambda message: message.text and message.text.lower() == "/health")
async def health_check(message: Message) -> None:
    """
    Healthcheck endpoint для проверки состояния приложения.
    
    Args:
        message: Объект сообщения от пользователя
    """
    try:
        # Проверяем конфигурацию
        config = get_config()
        if not config:
            await message.answer("❌ Конфигурация не загружена")
            return
            
        # Проверяем подключение к базе данных
        async with get_session() as session:
            await session.execute("SELECT 1")
            
        # Отправляем ответ о состоянии здоровья
        await message.answer("✅ Приложение работает нормально")
        logger.info("Health check passed")
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        await message.answer(f"❌ Ошибка healthcheck: {e}")


# Экспорт роутера для регистрации в основном приложении
__all__ = ["health_router"]