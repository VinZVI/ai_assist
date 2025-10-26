"""
@file: handlers/__init__.py
@description: Обработчики команд и сообщений Telegram бота
@dependencies: aiogram
@created: 2025-09-07
@updated: 2025-10-26
"""

from .admin import admin_router
from .callbacks import callback_router
from .health import health_router
from .help import help_router
from .language import language_router
from .limits import limits_router
from .message import message_router
from .onboarding import onboarding_router
from .premium import premium_router
from .profile import profile_router
from .start import start_router

# Список всех роутеров для регистрации
ROUTERS = [
    onboarding_router,  # Обработчик onboarding процесса
    start_router,  # Обработчик команды /start
    language_router,  # Обработчик команды /language
    help_router,  # Обработчик команды /help
    profile_router,  # Обработчик команды /profile
    limits_router,  # Обработчик команды /limits
    premium_router,  # Обработчик команды /premium
    callback_router,  # Обработчик callback запросов
    message_router,  # Обработчик текстовых сообщений
    health_router,  # Обработчик healthcheck
    admin_router,  # Админские команды
]

__all__ = [
    "ROUTERS",
    "admin_router",
    "callback_router",
    "health_router",
    "help_router",
    "language_router",
    "limits_router",
    "message_router",
    "onboarding_router",
    "premium_router",
    "profile_router",
    "start_router",
]
