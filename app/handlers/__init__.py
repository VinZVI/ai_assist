"""
@file: handlers/__init__.py
@description: Обработчики команд и сообщений Telegram бота
@dependencies: aiogram
@created: 2025-09-07
@updated: 2025-09-12
"""

from .message import message_router
from .start import start_router

# Список всех роутеров для регистрации
ROUTERS = [
    start_router,    # Обработчик команды /start
    message_router,  # Обработчик текстовых сообщений
]

__all__ = [
    "ROUTERS",
    "message_router",
    "start_router",
]
