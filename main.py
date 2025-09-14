#!/usr/bin/env python3
"""
@file: main.py
@description: Главная точка входа для AI-Компаньон Telegram бота
@dependencies: aiogram, asyncio, signal
@created: 2025-09-12
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from loguru import logger

from app.config import get_config
from app.database import init_db, close_db
from app.utils.logging import setup_logging
from app.handlers import ROUTERS
from app.services import close_ai_service


class AIAssistantBot:
    """Основной класс Telegram бота AI-Компаньон."""
    
    def __init__(self):
        self.config = get_config()
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None
        self._shutdown_event = asyncio.Event()
    
    def create_bot(self) -> Bot:
        """Создание экземпляра бота с настройками."""
        return Bot(
            token=self.config.telegram.bot_token if self.config.telegram else "dummy_token",
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                link_preview_is_disabled=True,
            )
        )
    
    def create_dispatcher(self) -> Dispatcher:
        """Создание диспетчера с middleware и обработчиками."""
        dp = Dispatcher()
        
        # Регистрация middleware будет здесь
        # self.register_middleware(dp)
        
        # Регистрация обработчиков
        self.register_handlers(dp)
        
        return dp
    
    def register_handlers(self, dp: Dispatcher) -> None:
        """Регистрация всех обработчиков."""
        for router in ROUTERS:
            dp.include_router(router)
        
        logger.info(f"✅ Зарегистрировано {len(ROUTERS)} роутеров")
    
    async def setup_bot_commands(self) -> None:
        """Настройка команд бота для меню."""
        if not self.bot:
            return
            
        commands = [
            BotCommand(command="start", description="🚀 Начать работу с ботом"),
            BotCommand(command="help", description="❓ Справка по командам"),
            BotCommand(command="profile", description="👤 Мой профиль"),
            BotCommand(command="limits", description="📊 Мои лимиты сообщений"),
            BotCommand(command="premium", description="⭐ Премиум доступ"),
        ]
        
        await self.bot.set_my_commands(commands)
        logger.info("✅ Команды бота настроены")
    
    async def startup(self) -> None:
        """Инициализация бота и подключений."""
        try:
            logger.info("🚀 Запуск AI-Компаньон бота...")
            
            # Инициализация базы данных
            logger.info("📊 Инициализация базы данных...")
            await init_db()
            
            # Создание бота и диспетчера
            self.bot = self.create_bot()
            self.dp = self.create_dispatcher()
            
            # Получение информации о боте
            bot_info = await self.bot.get_me()
            logger.info(f"🤖 Бот запущен: @{bot_info.username} ({bot_info.full_name})")
            
            # Настройка команд
            await self.setup_bot_commands()
            
            logger.success("✨ Бот успешно инициализирован и готов к работе!")
            
        except Exception as e:
            logger.error(f"💥 Ошибка при запуске бота: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Корректное завершение работы бота."""
        logger.info("🛑 Завершение работы бота...")
        
        try:
            # Остановка диспетчера
            if self.dp:
                await self.dp.stop_polling()
                logger.info("📡 Polling остановлен")
            
            # Закрытие сессии бота
            if self.bot:
                await self.bot.session.close()
                logger.info("🤖 Сессия бота закрыта")
            
            # Закрытие подключения к БД
            await close_db()
            
            # Закрытие AI сервиса
            await close_ai_service()
            
            logger.info("✅ Бот корректно завершил работу")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при завершении работы: {e}")
    
    def setup_signal_handlers(self) -> None:
        """Настройка обработчиков сигналов для корректного завершения."""
        if sys.platform != 'win32':
            # Unix-подобные системы
            for sig in (signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, self._signal_handler)
        else:
            # Windows
            signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов завершения."""
        logger.info(f"📡 Получен сигнал {signum}, инициирую завершение работы...")
        self._shutdown_event.set()
    
    async def run_polling(self) -> None:
        """Запуск бота в режиме polling."""
        if not self.dp or not self.bot:
            raise RuntimeError("Бот или диспетчер не инициализированы")
            
        logger.info("📡 Запуск в режиме polling...")
        
        try:
            # Запуск polling с graceful shutdown
            await self.dp.start_polling(
                self.bot,
                allowed_updates=self.dp.resolve_used_update_types(),
                drop_pending_updates=True,
            )
        except Exception as e:
            logger.error(f"💥 Ошибка в polling: {e}")
            raise
    
    async def run_webhook(self) -> None:
        """Запуск бота в режиме webhook (для продакшена)."""
        if not self.config.telegram or not self.config.telegram.webhook_url:
            raise ValueError("WEBHOOK_URL не настроен для режима webhook")
        
        if not self.bot or not self.dp:
            raise RuntimeError("Бот или диспетчер не инициализированы")
        
        logger.info(f"🌐 Запуск в режиме webhook: {self.config.telegram.webhook_url}")
        
        # Настройка webhook
        await self.bot.set_webhook(
            url=str(self.config.telegram.webhook_url),
            secret_token=self.config.telegram.webhook_secret,
            allowed_updates=self.dp.resolve_used_update_types(),
            drop_pending_updates=True,
        )
        
        logger.info("✅ Webhook настроен")
    
    async def run(self) -> None:
        """Главный метод запуска бота."""
        try:
            # Настройка обработчиков сигналов
            self.setup_signal_handlers()
            
            # Инициализация
            await self.startup()
            
            # Выбор режима работы
            if self.config.telegram and self.config.telegram.use_polling:
                await self.run_polling()
            else:
                await self.run_webhook()
                # В режиме webhook нужно поддерживать приложение активным
                await self._shutdown_event.wait()
            
        except KeyboardInterrupt:
            logger.info("⌨️ Получено прерывание с клавиатуры")
        except Exception as e:
            logger.error(f"💥 Критическая ошибка: {e}")
            raise
        finally:
            await self.shutdown()


@asynccontextmanager
async def lifespan() -> AsyncGenerator[None, None]:
    """Контекстный менеджер для управления жизненным циклом приложения."""
    bot_app = AIAssistantBot()
    
    try:
        await bot_app.startup()
        yield
    finally:
        await bot_app.shutdown()


async def main() -> None:
    """Главная функция приложения."""
    # Настройка логирования
    setup_logging()
    
    logger.info("🎯 AI-Компаньон: Telegram бот для эмоциональной поддержки")
    logger.info("📅 Версия: 1.0.0 | Дата: 2025-09-12")
    logger.info("-" * 60)
    
    try:
        # Создание и запуск бота
        bot_app = AIAssistantBot()
        await bot_app.run()
        
    except KeyboardInterrupt:
        logger.info("👋 Работа бота прервана пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка при запуске: {e}")
        sys.exit(1)
    finally:
        logger.info("🏁 Программа завершена")


if __name__ == "__main__":
    # Настройка asyncio для Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Запуск приложения
    asyncio.run(main())
