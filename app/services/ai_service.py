"""
@file: ai_service.py
@description: Сервис для интеграции с DeepSeek API для генерации ответов ИИ
@dependencies: httpx, asyncio, loguru, typing
@created: 2025-09-12
"""

import asyncio
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import httpx
from loguru import logger

from app.config import get_config


@dataclass
class AIResponse:
    """Структура ответа от AI сервиса."""
    content: str
    model: str
    tokens_used: int
    response_time: float
    cached: bool = False


@dataclass
class ConversationMessage:
    """Структура сообщения в диалоге."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime | None = None


class AIServiceError(Exception):
    """Базовый класс для ошибок AI сервиса."""


class APIConnectionError(AIServiceError):
    """Ошибка подключения к API."""


class APIRateLimitError(AIServiceError):
    """Ошибка превышения лимита запросов."""


class APIAuthenticationError(AIServiceError):
    """Ошибка аутентификации."""


class ResponseCache:
    """Простой кеш для ответов AI."""

    def __init__(self, ttl_seconds: int = 3600):
        self._cache: dict[str, dict[str, Any]] = {}
        self._ttl = ttl_seconds

    def _generate_key(self, messages: list[ConversationMessage], model: str) -> str:
        """Генерация ключа кеша из сообщений."""
        content = json.dumps([
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]) + model
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, messages: list[ConversationMessage], model: str) -> AIResponse | None:
        """Получение ответа из кеша."""
        key = self._generate_key(messages, model)

        if key in self._cache:
            entry = self._cache[key]
            if datetime.now() - entry["timestamp"] < timedelta(seconds=self._ttl):
                logger.debug(f"🎯 Найден кешированный ответ для ключа: {key[:8]}...")
                response = entry["response"]
                response.cached = True
                return response
            # Удаляем устаревший ключ
            del self._cache[key]

        return None

    def set(self, messages: list[ConversationMessage], model: str, response: AIResponse) -> None:
        """Сохранение ответа в кеш."""
        key = self._generate_key(messages, model)
        self._cache[key] = {
            "response": response,
            "timestamp": datetime.now(),
        }
        logger.debug(f"💾 Ответ сохранен в кеш с ключом: {key[:8]}...")

    def clear(self) -> None:
        """Очистка кеша."""
        self._cache.clear()
        logger.info("🧹 Кеш AI ответов очищен")


class AIService:
    """Сервис для работы с DeepSeek API."""

    def __init__(self):
        self.config = get_config()
        self._client: httpx.AsyncClient | None = None
        self._cache = ResponseCache(ttl_seconds=self.config.redis.cache_ttl)

        # Настройки по умолчанию
        self._default_temperature = self.config.deepseek.deepseek_temperature
        self._default_max_tokens = self.config.deepseek.deepseek_max_tokens
        self._timeout = self.config.deepseek.deepseek_timeout
        self._max_retries = 3
        self._retry_delay = 1.0

    async def _get_client(self) -> httpx.AsyncClient:
        """Получение HTTP клиента с настройками."""
        if self._client is None:
            headers = {
                "Authorization": f"Bearer {self.config.deepseek.deepseek_api_key}",
                "Content-Type": "application/json",
                "User-Agent": "AI-Assistant-Bot/1.0",
            }

            timeout = httpx.Timeout(
                connect=5.0,
                read=self._timeout,
                write=5.0,
                pool=5.0,
            )

            self._client = httpx.AsyncClient(
                base_url=self.config.deepseek.deepseek_base_url,
                headers=headers,
                timeout=timeout,
                limits=httpx.Limits(
                    max_keepalive_connections=5,
                    max_connections=10,
                ),
            )
            logger.info("🔗 HTTP клиент для DeepSeek API создан")

        return self._client

    async def close(self) -> None:
        """Закрытие HTTP клиента."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("🔌 HTTP клиент для DeepSeek API закрыт")

    def _prepare_messages(self, messages: list[ConversationMessage]) -> list[dict[str, str]]:
        """Подготовка сообщений для API."""
        prepared = []

        for msg in messages:
            prepared.append({
                "role": msg.role,
                "content": msg.content,
            })

        return prepared

    async def _make_api_request(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Выполнение запроса к API с retry логикой."""
        client = await self._get_client()

        payload = {
            "model": self.config.deepseek.deepseek_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        for attempt in range(self._max_retries):
            try:
                logger.debug(f"🚀 Отправка запроса к DeepSeek API (попытка {attempt + 1})")
                start_time = asyncio.get_event_loop().time()

                response = await client.post("/v1/chat/completions", json=payload)

                response_time = asyncio.get_event_loop().time() - start_time

                # Обработка различных статусов ответа
                if response.status_code == 200:
                    logger.info(f"✅ Успешный ответ от DeepSeek API за {response_time:.2f}с")
                    data = response.json()
                    return data

                if response.status_code == 401:
                    raise APIAuthenticationError("Неверный API ключ DeepSeek")

                if response.status_code == 429:
                    if attempt < self._max_retries - 1:
                        delay = self._retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"⏳ Rate limit достигнут. Ожидание {delay}с...")
                        await asyncio.sleep(delay)
                        continue
                    raise APIRateLimitError("Превышен лимит запросов к DeepSeek API")

                if response.status_code >= 500:
                    if attempt < self._max_retries - 1:
                        delay = self._retry_delay * (attempt + 1)
                        logger.warning(f"🔄 Ошибка сервера {response.status_code}. Повтор через {delay}с...")
                        await asyncio.sleep(delay)
                        continue
                    raise APIConnectionError(f"Ошибка сервера DeepSeek: {response.status_code}")

                raise APIConnectionError(f"Неожиданный статус ответа: {response.status_code}")

            except httpx.TimeoutException:
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (attempt + 1)
                    logger.warning(f"⏰ Timeout запроса. Повтор через {delay}с...")
                    await asyncio.sleep(delay)
                    continue
                raise APIConnectionError("Timeout при обращении к DeepSeek API")

            except httpx.ConnectError:
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (attempt + 1)
                    logger.warning(f"🌐 Ошибка подключения. Повтор через {delay}с...")
                    await asyncio.sleep(delay)
                    continue
                raise APIConnectionError("Не удалось подключиться к DeepSeek API")

        raise APIConnectionError("Исчерпаны все попытки подключения к API")

    async def generate_response(
        self,
        messages: list[ConversationMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
        use_cache: bool = True,
    ) -> AIResponse:
        """
        Генерация ответа от AI.
        
        Args:
            messages: Список сообщений диалога
            temperature: Температура генерации (0.0-2.0)
            max_tokens: Максимальное количество токенов
            use_cache: Использовать кеширование
        
        Returns:
            AIResponse: Ответ от AI сервиса
        """
        if not messages:
            raise ValueError("Список сообщений не может быть пустым")

        # Используем значения по умолчанию если не указаны
        temperature = temperature or self._default_temperature
        max_tokens = max_tokens or self._default_max_tokens

        # Валидация параметров
        if not 0.0 <= temperature <= 2.0:
            raise ValueError("Temperature должна быть от 0.0 до 2.0")

        if not 1 <= max_tokens <= 4000:
            raise ValueError("max_tokens должно быть от 1 до 4000")

        # Проверяем кеш
        if use_cache:
            cached_response = self._cache.get(messages, self.config.deepseek.deepseek_model)
            if cached_response:
                return cached_response

        try:
            # Подготавливаем сообщения
            prepared_messages = self._prepare_messages(messages)

            # Выполняем запрос
            start_time = asyncio.get_event_loop().time()
            data = await self._make_api_request(prepared_messages, temperature, max_tokens)
            response_time = asyncio.get_event_loop().time() - start_time

            # Извлекаем ответ
            if "choices" not in data or not data["choices"]:
                raise APIConnectionError("Некорректный формат ответа от DeepSeek API")

            choice = data["choices"][0]
            content = choice.get("message", {}).get("content", "")

            if not content:
                raise APIConnectionError("Пустой ответ от DeepSeek API")

            # Подсчитываем токены (приблизительно)
            tokens_used = data.get("usage", {}).get("total_tokens", len(content.split()) * 1.3)

            # Создаем объект ответа
            ai_response = AIResponse(
                content=content.strip(),
                model=self.config.deepseek.deepseek_model,
                tokens_used=int(tokens_used),
                response_time=response_time,
                cached=False,
            )

            # Сохраняем в кеш
            if use_cache:
                self._cache.set(messages, self.config.deepseek.deepseek_model, ai_response)

            logger.info(f"🤖 Сгенерирован ответ: {len(content)} символов, {tokens_used} токенов")
            return ai_response

        except AIServiceError:
            # Перебрасываем наши ошибки как есть
            raise

        except Exception as e:
            logger.exception("💥 Неожиданная ошибка при генерации ответа AI")
            raise AIServiceError(f"Неожиданная ошибка: {e!s}")

    async def generate_simple_response(self, user_message: str) -> AIResponse:
        """
        Упрощенный метод для генерации ответа на одно сообщение.
        
        Args:
            user_message: Сообщение пользователя
        
        Returns:
            AIResponse: Ответ от AI сервиса
        """
        messages = [
            ConversationMessage(
                role="system",
                content="Ты - эмпатичный AI-помощник. Отвечай доброжелательно и поддерживающе.",
            ),
            ConversationMessage(
                role="user",
                content=user_message,
            ),
        ]

        return await self.generate_response(messages)

    def clear_cache(self) -> None:
        """Очистка кеша ответов."""
        self._cache.clear()

    async def health_check(self) -> dict[str, Any]:
        """Проверка здоровья AI сервиса."""
        try:
            test_messages = [
                ConversationMessage(role="user", content="Hello"),
            ]

            start_time = asyncio.get_event_loop().time()
            response = await self.generate_response(test_messages, use_cache=False)
            response_time = asyncio.get_event_loop().time() - start_time

            return {
                "status": "healthy",
                "model": self.config.deepseek.deepseek_model,
                "response_time": response_time,
                "tokens_used": response.tokens_used,
                "cache_enabled": True,
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": self.config.deepseek.deepseek_model,
            }


# Глобальный экземпляр сервиса (создается лениво)
_ai_service_instance: AIService | None = None


def get_ai_service() -> AIService:
    """Получение экземпляра AI сервиса."""
    global _ai_service_instance

    if _ai_service_instance is None:
        _ai_service_instance = AIService()
        logger.info("🤖 AI сервис инициализирован")

    return _ai_service_instance


async def close_ai_service() -> None:
    """Закрытие AI сервиса."""
    global _ai_service_instance

    if _ai_service_instance:
        await _ai_service_instance.close()
        _ai_service_instance = None
        logger.info("🔌 AI сервис закрыт")


# Экспорт основных классов и функций
__all__ = [
    "AIResponse",
    "AIService",
    "AIServiceError",
    "APIAuthenticationError",
    "APIConnectionError",
    "APIRateLimitError",
    "ConversationMessage",
    "close_ai_service",
    "get_ai_service",
]
