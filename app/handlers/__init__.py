"""
@file: handlers/__init__.py
@description: Обработчики команд и сообщений Telegram бота
@dependencies: aiogram
@created: 2025-09-07
@updated: 2025-09-14
"""

from .callbacks import callback_router
from .health import health_router
from .message import message_router
from .start import start_router

# Список всех роутеров для регистрации
ROUTERS = [
    start_router,  # Обработчик команды /start
    callback_router,  # Обработчик callback запросов
    message_router,  # Обработчик текстовых сообщений
    health_router,  # Обработчик healthcheck
]

__all__ = [
    "ROUTERS",
    "callback_router",
    "health_router",
    "message_router",
    "start_router",
]
