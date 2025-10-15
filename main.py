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
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from loguru import logger

from app.config import get_config
from app.database import close_db, init_db
from app.handlers import ROUTERS
from app.lexicon.gettext import get_log_text
from app.services.ai_manager import close_ai_manager
from app.services.analytics import analytics_service
from app.services.monitoring import monitoring_service
from app.utils.logging import setup_logging


class AIAssistantBot:
    """Основной класс Telegram бота AI-Компаньон."""

    def __init__(self) -> None:
        self.config = get_config()
        self.bot: Bot | None = None
        self.dp: Dispatcher | None = None
        self._shutdown_event = asyncio.Event()

    def create_bot(self) -> Bot:
        """Создание экземпляра бота с настройками."""
        return Bot(
            token=self.config.telegram.bot_token
            if self.config.telegram
            else "dummy_token",
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                link_preview_is_disabled=True,
            ),
        )

    def create_dispatcher(self) -> Dispatcher:
        """Создание диспетчера с middleware и обработчиками."""
        dp = Dispatcher()

        # Регистрация middleware
        self.register_middleware(dp)

        # Регистрация обработчиков
        self.register_handlers(dp)

        return dp

    def register_middleware(self, dp: Dispatcher) -> None:
        """Регистрация middleware."""
        from app.middleware import (
            AdminMiddleware,
            AntiSpamMiddleware,
            AuthMiddleware,
            ContentFilterMiddleware,
            ConversationMiddleware,
            EmotionalProfilingMiddleware,
            LoggingMiddleware,
            MessageCountingMiddleware,
            MetricsMiddleware,
            RateLimitMiddleware,
            UserLanguageMiddleware,
        )

        # Создаем единственные экземпляры middleware
        logging_middleware = LoggingMiddleware()
        auth_middleware = AuthMiddleware()
        user_language_middleware = UserLanguageMiddleware()
        anti_spam_middleware = AntiSpamMiddleware()
        rate_limit_middleware = RateLimitMiddleware()
        content_filter_middleware = ContentFilterMiddleware()
        emotional_profiling_middleware = EmotionalProfilingMiddleware()
        conversation_middleware = ConversationMiddleware()
        message_counting_middleware = MessageCountingMiddleware()
        metrics_middleware = MetricsMiddleware()
        admin_middleware = AdminMiddleware()

        # Регистрация middleware в правильном порядке
        # 1. Логирование (первым для записи всех событий)
        dp.message.middleware(logging_middleware)
        dp.callback_query.middleware(logging_middleware)

        # 2. Аутентификация (для получения пользователя)
        dp.message.middleware(auth_middleware)
        dp.callback_query.middleware(auth_middleware)

        # 3. Проверка прав администратора
        dp.message.middleware(admin_middleware)
        dp.callback_query.middleware(admin_middleware)

        # 4. Управление языком пользователя
        dp.message.middleware(user_language_middleware)
        dp.callback_query.middleware(user_language_middleware)

        # 5. Защита от спама (после аутентификации)
        dp.message.middleware(anti_spam_middleware)
        dp.callback_query.middleware(anti_spam_middleware)

        # 6. Ограничение частоты запросов (после аутентификации)
        dp.message.middleware(rate_limit_middleware)
        dp.callback_query.middleware(rate_limit_middleware)

        # 7. Фильтрация контента (после аутентификации)
        dp.message.middleware(content_filter_middleware)
        dp.callback_query.middleware(content_filter_middleware)

        # 8. Профилирование эмоций пользователя (после аутентификации)
        dp.message.middleware(emotional_profiling_middleware)
        dp.callback_query.middleware(emotional_profiling_middleware)

        # 9. Сохранение диалогов
        dp.message.middleware(conversation_middleware)
        dp.callback_query.middleware(conversation_middleware)

        # 10. Подсчет сообщений пользователей (только для сообщений)
        dp.message.middleware(message_counting_middleware)
        # Не регистрируем для callback_query, так как они не считаются в лимиты

        # 11. Сбор метрик (последним для сбора полной информации)
        dp.message.middleware(metrics_middleware)
        dp.callback_query.middleware(metrics_middleware)

        logger.info(get_log_text("main.bot_registered_middleware"))

    def register_handlers(self, dp: Dispatcher) -> None:
        """Регистрация всех обработчиков."""
        for router in ROUTERS:
            dp.include_router(router)

        logger.info(
            get_log_text("main.bot_registered_routers").format(count=len(ROUTERS))
        )

    async def setup_bot_commands(self) -> None:
        """Настройка команд бота для меню."""
        if not self.bot:
            logger.warning("Bot is not initialized, skipping command setup")
            return

        try:
            # Get command descriptions from lexicon (using Russian as default)
            from app.lexicon.ru import LEXICON_RU

            help_commands = LEXICON_RU["help"]["commands"]

            # Convert lexicon commands to BotCommand objects
            commands = []
            for command, description in help_commands:
                # Remove the leading slash from command name for BotCommand
                command_name = command.lstrip("/")
                commands.append(
                    BotCommand(command=command_name, description=description)
                )

            logger.info(f"Setting up {len(commands)} bot commands")
            for cmd in commands:
                logger.debug(f"Command: {cmd.command} - {cmd.description}")

            await self.bot.set_my_commands(commands)
            logger.success(get_log_text("main.bot_commands_set"))

            # Verify commands were set
            try:
                set_commands = await self.bot.get_my_commands()
                logger.info(f"Successfully set {len(set_commands)} commands")
                for cmd in set_commands:
                    logger.debug(f"Set command: {cmd.command} - {cmd.description}")
            except Exception as verify_error:
                logger.warning(f"Could not verify set commands: {verify_error}")

        except Exception as e:
            logger.error(f"Failed to set bot commands: {e}")
            raise

    async def startup(self) -> None:
        """Инициализация бота и подключений."""
        try:
            logger.info(get_log_text("main.bot_starting"))

            # Инициализация базы данных
            logger.info(get_log_text("main.bot_db_initializing"))
            await init_db()

            # Создание бота и диспетчера
            self.bot = self.create_bot()
            self.dp = self.create_dispatcher()

            # Получение информации о боте
            bot_info = await self.bot.get_me()
            logger.info(
                get_log_text("main.bot_started").format(
                    username=bot_info.username, full_name=bot_info.full_name
                )
            )

            # Настройка команд
            await self.setup_bot_commands()

            # Запуск мониторинга и аналитики
            await monitoring_service.start_monitoring()
            await analytics_service.start_analytics_collection()

            logger.success(get_log_text("main.bot_initialized"))

        except Exception as e:
            logger.error(get_log_text("main.bot_shutdown_error").format(error=e))
            raise

    async def shutdown(self) -> None:
        """Корректное завершение работы бота."""
        logger.info(get_log_text("main.bot_shutdown_started"))

        try:
            # Остановка мониторинга и аналитики
            await monitoring_service.stop_monitoring()
            await analytics_service.stop_analytics_collection()

            # Остановка диспетчера с таймаутом
            if self.dp:
                try:
                    await asyncio.wait_for(self.dp.stop_polling(), timeout=10.0)
                    logger.info(get_log_text("main.bot_polling_stopped"))
                except TimeoutError:
                    logger.warning(get_log_text("main.bot_polling_stop_timeout"))
                except RuntimeError as e:
                    # Handle case when polling was not started
                    if "polling is not started" in str(e).lower():
                        logger.info(get_log_text("main.bot_polling_not_started"))
                    else:
                        logger.warning(
                            get_log_text("main.bot_error_stopping_polling").format(
                                error=e
                            )
                        )

            # Закрытие сессии бота с таймаутом
            if self.bot:
                try:
                    await asyncio.wait_for(self.bot.session.close(), timeout=5.0)
                    logger.info(get_log_text("main.bot_session_closed"))
                except TimeoutError:
                    logger.warning(get_log_text("main.bot_session_close_timeout"))

            # Закрытие подключения к БД с таймаутом
            try:
                await asyncio.wait_for(close_db(), timeout=5.0)
                logger.info(get_log_text("main.bot_db_closed"))
            except TimeoutError:
                logger.warning(get_log_text("main.bot_db_close_timeout"))

            # Закрытие AI менеджера с таймаутом
            try:
                await asyncio.wait_for(close_ai_manager(), timeout=5.0)
                logger.info(get_log_text("main.bot_ai_manager_closed"))
            except TimeoutError:
                logger.warning(get_log_text("main.bot_ai_manager_close_timeout"))

            logger.success(get_log_text("main.bot_shutdown_completed"))

        except Exception as e:
            logger.error(get_log_text("main.bot_shutdown_error").format(error=e))

    def setup_signal_handlers(self) -> None:
        """Настройка обработчиков сигналов для корректного завершения."""
        if sys.platform != "win32":
            # Unix-подобные системы
            for sig in (signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, self._signal_handler)
        else:
            # Windows
            signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame) -> None:  # noqa: ANN001
        """Обработчик сигналов завершения."""
        logger.info(get_log_text("main.bot_signal_received").format(signal=signum))
        self._shutdown_event.set()

    async def run_polling(self) -> None:
        """Запуск бота в режиме polling с поддержкой graceful shutdown."""
        if not self.dp or not self.bot:
            msg = "Бот или диспетчер не инициализированы"
            raise RuntimeError(msg)

        logger.info(get_log_text("main.bot_polling_started"))

        try:
            # Создаем задачу для polling
            polling_task = asyncio.create_task(
                self.dp.start_polling(
                    self.bot,
                    allowed_updates=self.dp.resolve_used_update_types(),
                    drop_pending_updates=True,
                ),
            )

            # Создаем задачу ожидания сигнала завершения
            shutdown_task = asyncio.create_task(self._shutdown_event.wait())

            # Ждем завершения любой из задач
            done, pending = await asyncio.wait(
                [polling_task, shutdown_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Отменяем оставшиеся задачи
            for task in pending:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

            # Если polling завершился с ошибкой, проверим это
            if polling_task in done:
                try:
                    await polling_task
                except Exception as e:
                    logger.error(
                        get_log_text("main.bot_error_in_polling").format(error=e)
                    )
                    raise

        except Exception as e:
            logger.error(get_log_text("main.bot_error_in_run_polling").format(error=e))
            raise

    async def run_webhook(self) -> None:
        """Запуск бота в режиме webhook (для продакшена)."""
        if not self.config.telegram or not self.config.telegram.webhook_url:
            msg = "WEBHOOK_URL не настроен для режима webhook"
            raise ValueError(msg)

        if not self.bot or not self.dp:
            msg = "Бот или диспетчер не инициализированы"
            raise RuntimeError(msg)

        logger.info(
            get_log_text("main.bot_webhook_started").format(
                url=self.config.telegram.webhook_url
            )
        )

        # Настройка webhook
        await self.bot.set_webhook(
            url=str(self.config.telegram.webhook_url),
            secret_token=self.config.telegram.webhook_secret,
            allowed_updates=self.dp.resolve_used_update_types(),
            drop_pending_updates=True,
        )

        logger.info(get_log_text("main.bot_webhook_set"))

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

            logger.info(get_log_text("main.bot_shutdown_initiated"))

        except KeyboardInterrupt:
            logger.info(get_log_text("main.bot_keyboard_interrupt"))
        except Exception as e:
            logger.error(get_log_text("main.bot_critical_error").format(error=e))
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
    # Настройка логирования с файловым выводом и улучшенным форматированием
    from pathlib import Path

    setup_logging(
        log_level="INFO",
        enable_console=True,
        log_file_path=Path("logs"),
        enable_json=True,
        enable_request_logging=True,
    )

    logger.info("🎯 AI-Компаньон: Telegram бот для эмоциональной поддержки")
    logger.info("📅 Версия: 1.0.0 | Дата: 2025-09-12")
    logger.info("-" * 60)

    bot_app = None
    try:
        # Создание и запуск бота
        bot_app = AIAssistantBot()
        await bot_app.run()

    except KeyboardInterrupt:
        logger.info(get_log_text("main.bot_user_interrupted"))
    except Exception as e:
        logger.error(get_log_text("main.bot_critical_error").format(error=e))
        if bot_app:
            with suppress(Exception):
                await bot_app.shutdown()
        sys.exit(1)
    finally:
        logger.info(get_log_text("main.bot_program_finished"))


if __name__ == "__main__":
    # Настройка asyncio для Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    try:
        # Запуск приложения
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception:
        sys.exit(1)
