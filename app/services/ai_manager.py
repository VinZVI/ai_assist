"""
@file: ai_manager.py
@description: Менеджер AI провайдеров с поддержкой fallback
@dependencies: pydantic, loguru, app.config, app.services.ai_providers
@created: 2025-09-12
"""

from datetime import UTC, datetime, timedelta, timezone
from typing import Any, ClassVar

from loguru import logger

from app.config import get_config
from app.services.ai_providers import OpenRouterProvider
from app.services.ai_providers.base import (
    AIProviderError,
    AIResponse,
    APIAuthenticationError,
    APIConnectionError,
    APIQuotaExceededError,
    APIRateLimitError,
    BaseAIProvider,
    ConversationMessage,
)


class AIManager:
    _providers: ClassVar[dict[str, BaseAIProvider]] = {}
    _cache: dict[str, dict[str, AIResponse | datetime]] = {}
    _ttl: int = 60
    _stats: ClassVar[dict[str, int]] = {
        "requests_total": 0,
        "requests_successful": 0,
        "requests_failed": 0,
        "fallback_used": 0,
    }
    _provider_stats: ClassVar[dict[str, dict[str, int]]] = {}

    def __init__(self) -> None:
        self._config = get_config()
        # Initialize providers - only OpenRouter now
        self._providers = {
            "openrouter": OpenRouterProvider(),
        }
        # Initialize provider stats
        for provider_name in self._providers:
            self._provider_stats[provider_name] = {
                "requests": 0,
                "successes": 0,
                "failures": 0,
            }

    def get_provider(self, name: str) -> BaseAIProvider | None:
        """Получение провайдера по имени."""
        return self._providers.get(name)

    async def generate_response(
        self,
        messages: list[ConversationMessage],
        prefer_provider: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        use_cache: bool = True,
    ) -> AIResponse:
        """
        Генерация ответа с поддержкой fallback между провайдерами.

        Args:
            messages: Список сообщений диалога
            prefer_provider: Предпочитаемый провайдер
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов
            use_cache: Использовать кеширование

        Returns:
            AIResponse: Ответ от AI провайдера
        """
        # Хешируем сообщения для кеширования
        messages_hash = hash(str([(m.role, m.content) for m in messages]))

        # Проверяем кеш
        if use_cache and messages_hash in self._cache:
            entry = self._cache[messages_hash]
            if datetime.now(UTC) - entry["timestamp"] < timedelta(seconds=self._ttl):
                logger.debug("🎯 Найден кешированный ответ")
                cached_response = entry["response"]
                return AIResponse(
                    content=cached_response.content,
                    model=cached_response.model,
                    tokens_used=cached_response.tokens_used,
                    response_time=0.01,  # Очень быстрый ответ из кеша
                    provider=cached_response.provider,
                    cached=True,
                )

        # Увеличиваем счетчик запросов
        self._stats["requests_total"] += 1

        # Only one provider now - OpenRouter
        provider_name = "openrouter"
        provider = self._providers[provider_name]

        # Проверяем настройку провайдера
        if not provider.is_configured():
            logger.debug(f"⏭️ Провайдер {provider_name} не настроен, пропускаем")
            msg = "OpenRouter API не настроен. Проверьте OPENROUTER_API_KEY в .env"
            raise APIAuthenticationError(
                msg,
                provider_name,
                "not_configured",
            )

        try:
            # Увеличиваем счетчик запросов к провайдеру
            self._provider_stats[provider_name]["requests"] += 1

            # Генерируем ответ
            start_time = datetime.now(UTC)
            response = await provider.generate_response(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            response_time = (datetime.now(UTC) - start_time).total_seconds()

            # Обновляем статистику успеха
            self._stats["requests_successful"] += 1
            self._provider_stats[provider_name]["successes"] += 1

            # Сохраняем в кеш
            if use_cache:
                self._cache[messages_hash] = {
                    "response": response,
                    "timestamp": datetime.now(UTC),
                }

            logger.info(
                f"🤖 Ответ получен от {provider_name}: "
                f"{len(response.content)} символов, "
                f"{response.tokens_used} токенов, "
                f"{response_time:.2f}с"
            )

            return response

        except (
            APIAuthenticationError,
            APIConnectionError,
            APIQuotaExceededError,
            APIRateLimitError,
        ) as e:
            # Обновляем статистику ошибок
            self._stats["requests_failed"] += 1
            self._provider_stats[provider_name]["failures"] += 1

            logger.error(f"💥 Ошибка провайдера {provider_name}: {e}")
            raise AIProviderError(
                f"AI провайдер недоступен: {e!s}",
                provider_name,
            ) from e

    async def generate_simple_response(self, prompt: str) -> AIResponse:
        """
        Генерация простого ответа для быстрых запросов.

        Args:
            prompt: Текст запроса

        Returns:
            AIResponse: Ответ от AI провайдера
        """
        messages = [
            ConversationMessage(
                role="user",
                content=prompt,
            ),
        ]
        return await self.generate_response(messages)

    async def health_check(self) -> dict[str, Any]:
        """
        Проверка здоровья всех провайдеров.

        Returns:
            dict: Статус и метрики менеджера и провайдеров
        """
        provider_health = {}
        all_healthy = True

        for provider_name, provider in self._providers.items():
            try:
                if not provider.is_configured():
                    provider_health[provider_name] = {
                        "status": "not_configured",
                        "error": "Провайдер не настроен",
                    }
                    all_healthy = False
                    continue

                health_result = await provider.health_check()
                provider_health[provider_name] = health_result

                if health_result.get("status") != "healthy":
                    all_healthy = False

            except Exception as e:
                provider_health[provider_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                all_healthy = False

        return {
            "manager_status": "healthy" if all_healthy else "degraded",
            "providers": provider_health,
        }

    async def close(self) -> None:
        """Закрытие всех провайдеров и освобождение ресурсов."""
        for provider in self._providers.values():
            try:
                await provider.close()
            except Exception as e:
                logger.warning(f"Ошибка при закрытии провайдера {provider.name}: {e}")

        # Очищаем кеш
        self._cache.clear()
        logger.info("🔌 Все провайдеры закрыты, кеш очищен")

    def get_stats(self) -> dict[str, Any]:
        """
        Получение статистики использования.

        Returns:
            dict: Статистика менеджера и провайдеров
        """
        return {
            "requests_total": self._stats["requests_total"],
            "requests_successful": self._stats["requests_successful"],
            "requests_failed": self._stats["requests_failed"],
            "fallback_used": self._stats["fallback_used"],
            "provider_stats": self._provider_stats,
        }

    def clear_cache(self) -> None:
        """Очистка кеша."""
        self._cache.clear()
        logger.info("🧹 Кеш AIManager очищен")


# Глобальный экземпляр менеджера (создается лениво)
_ai_manager_instance: AIManager | None = None


def get_ai_manager() -> AIManager:
    """Получение экземпляра AI менеджера."""
    global _ai_manager_instance

    if _ai_manager_instance is None:
        _ai_manager_instance = AIManager()
        logger.info("🤖 AI менеджер инициализирован")

    return _ai_manager_instance


async def close_ai_manager() -> None:
    """Закрытие AI менеджера."""
    global _ai_manager_instance

    if _ai_manager_instance:
        await _ai_manager_instance.close()
        _ai_manager_instance = None
        logger.info("🔌 AI менеджер закрыт")


# Экспорт основных классов и функций
__all__ = [
    "AIManager",
    "close_ai_manager",
    "get_ai_manager",
]
