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

        # Регистрация middleware будет здесь
        # self.register_middleware(dp)

        # Регистрация обработчиков
        self.register_handlers(dp)

        return dp

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
            return

        # Get command descriptions from lexicon (using Russian as default)
        from app.lexicon.ru import LEXICON_RU
        help_commands = LEXICON_RU["help"]["commands"]

        # Convert lexicon commands to BotCommand objects
        commands = []
        for command, description in help_commands:
            # Remove the leading slash from command name for BotCommand
            command_name = command.lstrip('/')
            commands.append(BotCommand(command=command_name, description=description))

        await self.bot.set_my_commands(commands)
        logger.info(get_log_text("main.bot_commands_set"))

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

            logger.success(get_log_text("main.bot_initialized"))

        except Exception as e:
            logger.error(get_log_text("main.bot_shutdown_error").format(error=e))
            raise

    async def shutdown(self) -> None:
        """Корректное завершение работы бота."""
        logger.info(get_log_text("main.bot_shutdown_started"))

        try:
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
