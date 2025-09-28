"""
@file: ai_providers/openrouter.py
@description: Провайдер AI для OpenRouter API
@dependencies: httpx, loguru, app.config, .base
@created: 2025-09-20
"""

import asyncio
from typing import Any

import httpx
from loguru import logger

from app.config import get_config

from .base import (
    AIResponse,
    APIAuthenticationError,
    APIConnectionError,
    APIQuotaExceededError,
    APIRateLimitError,
    BaseAIProvider,
    ConversationMessage,
)


class OpenRouterProvider(BaseAIProvider):
    """Провайдер AI для OpenRouter API."""

    def __init__(self) -> None:
        super().__init__("openrouter")
        self.config = get_config().openrouter
        self._client: httpx.AsyncClient | None = None
        self._max_retries = 3
        self._retry_delay = 1.0

    @property
    def provider_name(self) -> str:
        return "openrouter"

    async def _get_client(self) -> httpx.AsyncClient:
        """Получение HTTP клиента с настройками для OpenRouter."""
        if self._client is None:
            headers = {
                "Authorization": f"Bearer {self.config.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.config.openrouter_site_url,
                "X-Title": self.config.openrouter_app_name,
            }

            timeout = httpx.Timeout(
                connect=5.0,
                read=self.config.openrouter_timeout,
                write=5.0,
                pool=5.0,
            )

            self._client = httpx.AsyncClient(
                base_url=self.config.openrouter_base_url,
                headers=headers,
                timeout=timeout,
                limits=httpx.Limits(
                    max_keepalive_connections=5,
                    max_connections=10,
                ),
            )
            logger.info("🔗 HTTP клиент для OpenRouter API создан")

        return self._client

    async def close(self) -> None:
        """Закрытие HTTP клиента."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("🔌 HTTP клиент для OpenRouter API закрыт")

    def is_configured(self) -> bool:
        """Проверка правильности настройки провайдера."""
        return self.config.is_configured()

    async def _make_api_request(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Выполнение запроса к OpenRouter API с retry логикой."""
        client = await self._get_client()

        payload = {
            "model": self.config.openrouter_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        for attempt in range(self._max_retries):
            try:
                logger.debug(
                    f"🚀 Отправка запроса к OpenRouter API (попытка {attempt + 1})",
                )
                start_time = asyncio.get_event_loop().time()

                response = await client.post("/chat/completions", json=payload)
                response_time = self._calculate_response_time(start_time)

                # Обработка различных статусов ответа
                if response.status_code == 200:
                    logger.info(
                        f"✅ Успешный ответ от OpenRouter API за {response_time:.2f}с",
                    )
                    return response.json()

                if response.status_code == 401:
                    msg = "Неверный API ключ OpenRouter"
                    raise APIAuthenticationError(
                        msg,
                        self.provider_name,
                        "401",
                    )

                if response.status_code == 402:
                    msg = (
                        "Недостаточно средств на счете OpenRouter API. "
                        "Пополните баланс в личном кабинете OpenRouter."
                    )
                    raise APIQuotaExceededError(
                        msg,
                        self.provider_name,
                        "402",
                    )

                if response.status_code == 429:
                    if attempt < self._max_retries - 1:
                        delay = self._retry_delay * (2**attempt)
                        logger.warning(
                            f"⏳ Rate limit достигнут в OpenRouter. "
                            f"Ожидание {delay}с...",
                        )
                        await asyncio.sleep(delay)
                        continue
                    msg = "Превышен лимит запросов к OpenRouter API"
                    raise APIRateLimitError(
                        msg,
                        self.provider_name,
                        "429",
                    )

                if response.status_code >= 500:
                    if attempt < self._max_retries - 1:
                        delay = self._retry_delay * (attempt + 1)
                        logger.warning(
                            f"🔄 Ошибка сервера OpenRouter {response.status_code}. "
                            f"Повтор через {delay}с...",
                        )
                        await asyncio.sleep(delay)
                        continue
                    msg = f"Ошибка сервера OpenRouter: {response.status_code}"
                    raise APIConnectionError(
                        msg,
                        self.provider_name,
                        str(response.status_code),
                    )

                # Обработка других ошибок
                error_text = ""
                try:
                    error_data = response.json()
                    error_text = error_data.get("error", {}).get("message", "")
                except:
                    error_text = response.text

                msg = (
                    f"Неожиданный статус ответа OpenRouter: {response.status_code}. "
                    f"{error_text}"
                )
                raise APIConnectionError(
                    msg,
                    self.provider_name,
                    str(response.status_code),
                )

            except httpx.TimeoutException:
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (attempt + 1)
                    logger.warning(
                        f"⏰ Timeout запроса к OpenRouter. Повтор через {delay}с...",
                    )
                    await asyncio.sleep(delay)
                    continue
                msg = "Timeout при обращении к OpenRouter API"
                raise APIConnectionError(
                    msg,
                    self.provider_name,
                    "timeout",
                )

            except httpx.ConnectError:
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (attempt + 1)
                    logger.warning(
                        f"🌐 Ошибка подключения к OpenRouter. Повтор через {delay}с...",
                    )
                    await asyncio.sleep(delay)
                    continue
                msg = "Не удалось подключиться к OpenRouter API"
                raise APIConnectionError(
                    msg,
                    self.provider_name,
                    "connection_error",
                )

        msg = "Исчерпаны все попытки подключения к OpenRouter API"
        raise APIConnectionError(
            msg,
            self.provider_name,
            "max_retries_exceeded",
        )

    async def generate_response(
        self,
        messages: list[ConversationMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AIResponse:
        """Генерация ответа от OpenRouter AI."""
        if not messages:
            msg = "Список сообщений не может быть пустым"
            raise ValueError(msg)

        if not self.is_configured():
            msg = "OpenRouter API не настроен. Проверьте OPENROUTER_API_KEY в .env"
            raise APIAuthenticationError(
                msg,
                self.provider_name,
                "not_configured",
            )

        # Используем значения по умолчанию если не указаны
        temperature = temperature or self.config.openrouter_temperature
        max_tokens = max_tokens or self.config.openrouter_max_tokens

        # Валидация параметров
        if not 0.0 <= temperature <= 2.0:
            msg = "Temperature должна быть от 0.0 до 2.0"
            raise ValueError(msg)

        if not 1 <= max_tokens <= 8000:
            msg = "max_tokens должно быть от 1 до 8000"
            raise ValueError(msg)

        try:
            # Подготавливаем сообщения
            prepared_messages = self._prepare_messages(messages)

            # Выполняем запрос
            start_time = asyncio.get_event_loop().time()
            data = await self._make_api_request(
                prepared_messages,
                temperature,
                max_tokens,
            )
            response_time = self._calculate_response_time(start_time)

            # Извлекаем ответ
            if "choices" not in data or not data["choices"]:
                msg = "Некорректный формат ответа от OpenRouter API"
                raise APIConnectionError(
                    msg,
                    self.provider_name,
                    "invalid_response",
                )

            choice = data["choices"][0]
            content = choice.get("message", {}).get("content", "")

            if not content:
                msg = "Пустой ответ от OpenRouter API"
                raise APIConnectionError(
                    msg,
                    self.provider_name,
                    "empty_response",
                )

            # Подсчитываем токены
            tokens_used = data.get("usage", {}).get(
                "total_tokens",
                len(content.split()) * 1.3,
            )

            # Метаданные
            metadata = {
                "model_used": data.get("model", self.config.openrouter_model),
                "finish_reason": choice.get("finish_reason"),
                "usage": data.get("usage", {}),
            }

            # Создаем объект ответа
            ai_response = AIResponse(
                content=content.strip(),
                model=self.config.openrouter_model,
                tokens_used=int(tokens_used),
                response_time=response_time,
                provider=self.provider_name,
                cached=False,
                metadata=metadata,
            )

            logger.info(
                f"🤖 OpenRouter ответ: {len(content)} символов, "
                f"{tokens_used} токенов, {response_time:.2f}с",
            )
            return ai_response

        except Exception as e:
            if isinstance(
                e,
                APIConnectionError
                | APIRateLimitError
                | APIAuthenticationError
                | APIQuotaExceededError,
            ):
                raise

            logger.exception("💥 Неожиданная ошибка при генерации ответа OpenRouter")
            msg = f"Неожиданная ошибка OpenRouter: {e!s}"
            raise APIConnectionError(
                msg,
                self.provider_name,
                "unexpected_error",
            )

    async def health_check(self) -> dict[str, Any]:
        """Проверка здоровья OpenRouter API."""
        try:
            if not self.is_configured():
                return {
                    "status": "unhealthy",
                    "error": "OpenRouter API не настроен",
                    "provider": self.provider_name,
                }

            test_messages = [
                ConversationMessage(role="user", content="Hello"),
            ]

            start_time = asyncio.get_event_loop().time()
            response = await self.generate_response(test_messages)
            response_time = self._calculate_response_time(start_time)

            return {
                "status": "healthy",
                "provider": self.provider_name,
                "model": self.config.openrouter_model,
                "response_time": response_time,
                "tokens_used": response.tokens_used,
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "provider": self.provider_name,
                "model": self.config.openrouter_model,
            }


# Экспорт провайдера
__all__ = ["OpenRouterProvider"]
