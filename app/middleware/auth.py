"""Middleware для автоматического получения/создания пользователя."""

from collections.abc import Awaitable, Callable
from typing import Any, ClassVar, cast

from aiogram.types import CallbackQuery, InaccessibleMessage, Message, TelegramObject
from aiogram.types import User as TelegramUser
from loguru import logger

from app.config import get_config
from app.lexicon.gettext import get_log_text
from app.middleware.base import BaseAIMiddleware
from app.models.user import User as UserModel
from app.services.cache_service import cache_service
from app.services.user_service import get_or_update_user


class AuthMiddleware(BaseAIMiddleware):
    """Middleware для автоматического получения/создания пользователя."""

    # Статистика по аутентификации
    _auth_stats: ClassVar[dict[str, int]] = {
        "users_authenticated": 0,
        "users_created": 0,
        "auth_errors": 0,
    }

    def __init__(self) -> None:
        """Инициализация AuthMiddleware."""
        super().__init__()
        self.cache_service = cache_service
        self.config = get_config()
        # Инициализация Redis кеша
        import asyncio

        self._redis_init_task = asyncio.create_task(self._initialize_redis_cache())
        logger.info(get_log_text("middleware.auth_middleware_initialized"))

    async def _initialize_redis_cache(self) -> None:
        """Асинхронная инициализация Redis кеша."""
        try:
            await self.cache_service.initialize_redis_cache()
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")

    async def check_terms_versions(self, user: UserModel) -> bool:
        """
        Проверка актуальности версий соглашений.

        Args:
            user: Пользователь для проверки

        Returns:
            bool: True если требуется повторная валидация
        """
        current_versions = {
            "terms": self.config.compliance.terms_version,
            "privacy": self.config.compliance.privacy_version,
            "guidelines": self.config.compliance.guidelines_version,
        }

        return (
            user.terms_version != current_versions["terms"]
            or user.privacy_version != current_versions["privacy"]
            or user.guidelines_version != current_versions["guidelines"]
        )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Обработка события с аутентификацией пользователя.

        Args:
            handler: Следующий обработчик в цепочке
            event: Событие Telegram
            data: Данные контекста обработки

        Returns:
            Результат выполнения следующего обработчика
        """
        # Получаем пользователя Telegram из события
        telegram_user: TelegramUser | None = None
        message: Message | None = None

        # Проверяем разные типы событий для получения пользователя и сообщения
        if isinstance(event, Message) and event.from_user:
            telegram_user = event.from_user
            message = event
        elif isinstance(event, CallbackQuery) and event.from_user:
            telegram_user = event.from_user
            # Для CallbackQuery проверяем, что message существует и доступен для редактирования
            if event.message and not isinstance(event.message, InaccessibleMessage):
                message = event.message

        # Только если у нас есть и пользователь, и сообщение, пытаемся аутентифицировать
        if telegram_user and message:
            try:
                # Проверяем кеш первым делом
                user = await self.cache_service.get_user(telegram_user.id)

                if not user:
                    # Если нет в кеше - загружаем из БД
                    user = await get_or_update_user(message)

                    if user:
                        # Кешируем пользователя
                        await self.cache_service.set_user(user)
                        logger.debug(
                            get_log_text("middleware.user_cached").format(
                                user_id=user.id, username=user.username or "No username"
                            )
                        )
                    else:
                        # Ошибка при создании/получении пользователя
                        self._auth_stats["auth_errors"] += 1
                        logger.warning(
                            get_log_text("middleware.user_auth_failed").format(
                                telegram_id=telegram_user.id
                            )
                        )
                else:
                    # Пользователь найден в кеше
                    logger.debug(
                        get_log_text("middleware.user_cache_hit").format(
                            user_id=user.id, username=user.username or "No username"
                        )
                    )

                if user:
                    # Добавляем проверку актуальности верификации
                    if user.is_fully_verified:
                        # Проверяем актуальность версий соглашений
                        needs_revalidation = await self.check_terms_versions(user)
                        if needs_revalidation:
                            user.verification_status = "expired"
                            from app.core.dependencies import container

                            user_service = container.get("user_service")
                            await user_service.update_user(user)
                            # Обновляем кеш, чтобы состояние было консистентным
                            await self.cache_service.set_user(user)
                            logger.info(
                                f"User {user.telegram_id} verification expired due to terms update"
                            )

                    # Проверяем статусы верификации (pending/expired/rejected)
                    if not user.is_fully_verified:
                        is_allowed = False

                        if isinstance(message, Message) and message.text:
                            command = message.text.split()[0]
                            allowed_commands = ["/start", "/help", "/support"]
                            is_allowed = command in allowed_commands
                        elif isinstance(event, CallbackQuery):
                            callback_data = event.data or ""
                            allowed_prefixes = ["onboarding:", "consent:"]
                            is_allowed = any(
                                callback_data.startswith(prefix)
                                for prefix in allowed_prefixes
                            )

                        if not is_allowed:
                            # Вместо просто отправки сообщения, перенаправляем на процесс верификации
                            verification_message = self._get_verification_message(
                                user.verification_status
                            )
                            try:
                                callback_answered = False
                                if isinstance(message, Message):
                                    # Отправляем сообщение с кнопкой для начала верификации
                                    await message.answer(
                                        verification_message,
                                        reply_markup=self._get_verification_keyboard()
                                    )
                                elif isinstance(event, CallbackQuery):
                                    # For callback queries, we need to be more careful
                                    if (
                                        event.message
                                        and not isinstance(
                                            event.message, InaccessibleMessage
                                        )
                                    ):
                                        try:
                                            # Try to edit the message first
                                            await event.message.edit_text(
                                                verification_message,
                                                reply_markup=self._get_verification_keyboard()
                                            )
                                            logger.info(f"Edited message for unverified user {user.telegram_id}")
                                        except Exception as edit_error:
                                            # If editing fails, send a new message
                                            logger.warning(f"Failed to edit message for user {user.telegram_id}: {edit_error}")
                                            try:
                                                await event.message.answer(
                                                    verification_message,
                                                    reply_markup=self._get_verification_keyboard()
                                                )
                                                logger.info(f"Sent new message for unverified user {user.telegram_id}")
                                            except Exception as send_error:
                                                logger.error(f"Failed to send message to user {user.telegram_id}: {send_error}")
                                    # Always answer the callback query
                                    await event.answer()
                                    callback_answered = True
                            except Exception as e:
                                logger.error(
                                    f"Error notifying user about verification: {e}"
                                )
                            finally:
                                # Ensure callback is always answered to prevent loading indicator
                                if isinstance(event, CallbackQuery) and not callback_answered:
                                    try:
                                        await event.answer()
                                    except Exception:
                                        pass  # Already handled
                            return None

                    # Добавляем пользователя в данные контекста
                    data["user"] = user
                    self._auth_stats["users_authenticated"] += 1

                    logger.info(
                        get_log_text("middleware.user_authenticated").format(
                            user_id=user.id, username=user.username or "No username"
                        )
                    )

            except Exception as e:
                self._auth_stats["auth_errors"] += 1
                logger.error(
                    get_log_text("middleware.user_auth_error").format(
                        error=str(e),
                        telegram_id=telegram_user.id if telegram_user else "unknown",
                    )
                )

        # Передаем управление следующему обработчику
        return await handler(event, data)

    @classmethod
    def get_auth_stats(cls) -> dict[str, int]:
        """
        Получение статистики аутентификации.

        Returns:
            Словарь со статистикой аутентификации
        """
        return cls._auth_stats.copy()

    @classmethod
    def reset_auth_stats(cls) -> None:
        """Сброс статистики аутентификации."""
        cls._auth_stats = {
            "users_authenticated": 0,
            "users_created": 0,
            "auth_errors": 0,
        }

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Получение статистики кеша.

        Returns:
            Словарь со статистикой кеша
        """
        return self.cache_service.get_cache_stats()

    def _get_verification_message(self, status: str) -> str:
        """
        Возвращает текст для уведомления пользователя о необходимости верификации.

        Args:
            status: verification_status пользователя

        Returns:
            Строку с сообщением
        """
        if status == "expired":
            return (
                "⚠️ Ваша верификация истекла из-за обновления условий использования.\n\n"
                "Нажмите кнопку ниже, чтобы пройти процесс заново."
            )
        if status == "rejected":
            return (
                "❌ Верификация была отклонена.\n\n"
                "Если хотите продолжить пользоваться ботом, пройдите регистрацию заново."
            )
        return (
            "⚠️ Для использования бота необходимо завершить регистрацию.\n\n"
            "Пожалуйста, нажмите кнопку ниже, чтобы начать процесс верификации."
        )

    def _get_verification_keyboard(self):
        """
        Возвращает клавиатуру для начала верификации.
        
        Returns:
            InlineKeyboardMarkup: Клавиатура с кнопкой для начала верификации
        """
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Начать регистрацию", callback_data="onboarding:start")]
            ]
        )
        return keyboard
