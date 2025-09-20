"""
@file: ai_manager.py
@description: Менеджер AI провайдеров с поддержкой fallback и балансировки нагрузки
@dependencies: loguru, app.config, .ai_providers
@created: 2025-09-20
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any

from loguru import logger

from app.config import get_config
from .ai_providers import (
    AIResponse,
    ConversationMessage,
    AIProviderError,
    APIConnectionError,
    APIRateLimitError,
    APIAuthenticationError,
    APIQuotaExceededError,
    DeepSeekProvider,
    OpenRouterProvider,
)


class ResponseCache:
    """Простой кеш для ответов AI с поддержкой нескольких провайдеров."""

    def __init__(self, ttl_seconds: int = 3600):
        self._cache: dict[str, dict[str, Any]] = {}
        self._ttl = ttl_seconds

    def _generate_key(self, messages: list[ConversationMessage], provider: str) -> str:
        """Генерация ключа кеша из сообщений и провайдера."""
        content = json.dumps([
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]) + provider
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, messages: list[ConversationMessage], provider: str) -> AIResponse | None:
        """Получение ответа из кеша."""
        key = self._generate_key(messages, provider)

        if key in self._cache:
            entry = self._cache[key]
            if datetime.now() - entry["timestamp"] < timedelta(seconds=self._ttl):
                logger.debug(f"🎯 Найден кешированный ответ для {provider}: {key[:8]}...")
                response = entry["response"]
                response.cached = True
                return response
            # Удаляем устаревший ключ
            del self._cache[key]

        return None

    def set(self, messages: list[ConversationMessage], provider: str, response: AIResponse) -> None:
        """Сохранение ответа в кеш."""
        key = self._generate_key(messages, provider)
        self._cache[key] = {
            "response": response,
            "timestamp": datetime.now(),
        }
        logger.debug(f"💾 Ответ {provider} сохранен в кеш: {key[:8]}...")

    def clear(self) -> None:
        """Очистка кеша."""
        self._cache.clear()
        logger.info("🧹 Кеш AI ответов очищен")


class AIManager:
    """Менеджер AI провайдеров с поддержкой fallback и балансировки."""
    
    def __init__(self):
        self.config = get_config()
        self.provider_config = self.config.ai_provider
        self._cache = ResponseCache(ttl_seconds=self.config.redis.cache_ttl)
        
        # Инициализация провайдеров
        self._providers: dict[str, Any] = {}
        self._initialize_providers()
        
        # Статистика
        self._stats = {
            "requests_total": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "fallback_used": 0,
            "provider_stats": {},
        }
    
    def _initialize_providers(self) -> None:
        """Инициализация всех доступных провайдеров."""
        logger.info("🔧 Инициализация AI провайдеров...")
        
        # DeepSeek провайдер
        try:
            deepseek = DeepSeekProvider()
            if deepseek.is_configured():
                self._providers["deepseek"] = deepseek
                logger.info("✅ DeepSeek провайдер инициализирован")
            else:
                logger.warning("⚠️ DeepSeek провайдер не настроен")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации DeepSeek: {e}")
        
        # OpenRouter провайдер
        try:
            openrouter = OpenRouterProvider()
            if openrouter.is_configured():
                self._providers["openrouter"] = openrouter
                logger.info("✅ OpenRouter провайдер инициализирован")
            else:
                logger.warning("⚠️ OpenRouter провайдер не настроен")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации OpenRouter: {e}")
        
        if not self._providers:
            logger.error("❌ Ни один AI провайдер не настроен!")
        else:
            logger.info(f"🎯 Активные провайдеры: {list(self._providers.keys())}")
    
    def get_provider(self, provider_name: str) -> Any | None:
        """Получение провайдера по имени."""
        return self._providers.get(provider_name)
    
    def get_primary_provider(self) -> Any | None:
        """Получение основного провайдера."""
        return self.get_provider(self.provider_config.primary_provider)
    
    def get_fallback_provider(self) -> Any | None:
        """Получение резервного провайдера."""
        return self.get_provider(self.provider_config.fallback_provider)
    
    async def _try_provider(
        self, 
        provider: Any, 
        messages: list[ConversationMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
        use_cache: bool = True,
    ) -> AIResponse:
        """Попытка получить ответ от конкретного провайдера."""
        provider_name = provider.provider_name
        
        # Проверяем кеш
        if use_cache:
            cached_response = self._cache.get(messages, provider_name)
            if cached_response:
                logger.info(f"🎯 Использован кешированный ответ от {provider_name}")
                return cached_response
        
        # Проверяем доступность провайдера
        if not await provider.is_available():
            raise APIConnectionError(
                f"Провайдер {provider_name} недоступен",
                provider_name,
                "unavailable"
            )
        
        # Выполняем запрос
        logger.info(f"🚀 Запрос к {provider_name}...")
        response = await provider.generate_response(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Сохраняем в кеш
        if use_cache:
            self._cache.set(messages, provider_name, response)
        
        # Обновляем статистику
        self._update_stats(provider_name, success=True)
        
        return response
    
    async def generate_response(
        self,
        messages: list[ConversationMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
        use_cache: bool = True,
        prefer_provider: str | None = None,
    ) -> AIResponse:
        """
        Генерация ответа с автоматическим fallback между провайдерами.
        
        Args:
            messages: Список сообщений диалога
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов
            use_cache: Использовать кеширование
            prefer_provider: Предпочтительный провайдер (игнорирует настройки primary/fallback)
        
        Returns:
            AIResponse: Ответ от AI провайдера
            
        Raises:
            AIProviderError: Если все провайдеры недоступны
        """
        if not messages:
            raise ValueError("Список сообщений не может быть пустым")
        
        self._stats["requests_total"] += 1
        
        # Определяем порядок провайдеров
        if prefer_provider and prefer_provider in self._providers:
            provider_order = [prefer_provider]
            # Добавляем остальные как fallback если включен
            if self.provider_config.enable_fallback:
                provider_order.extend([
                    name for name in self._providers.keys() 
                    if name != prefer_provider
                ])
        else:
            provider_order = [self.provider_config.primary_provider]
            if (self.provider_config.enable_fallback and 
                self.provider_config.fallback_provider != self.provider_config.primary_provider):
                provider_order.append(self.provider_config.fallback_provider)
        
        last_error = None
        
        for i, provider_name in enumerate(provider_order):
            provider = self.get_provider(provider_name)
            if not provider:
                logger.warning(f"⚠️ Провайдер {provider_name} не найден")
                continue
            
            try:
                logger.info(f"🎯 Попытка {i+1}: использование {provider_name}")
                response = await self._try_provider(
                    provider=provider,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    use_cache=use_cache,
                )
                
                if i > 0:  # Fallback был использован
                    self._stats["fallback_used"] += 1
                    logger.info(f"🔄 Fallback успешен: {provider_name}")
                
                self._stats["requests_successful"] += 1
                return response
                
            except (APIQuotaExceededError, APIAuthenticationError) as e:
                # Критические ошибки - не пытаемся fallback
                logger.error(f"❌ Критическая ошибка {provider_name}: {e}")
                last_error = e
                self._update_stats(provider_name, success=False)
                break
                
            except (APIConnectionError, APIRateLimitError) as e:
                # Временные ошибки - можно попробовать fallback
                logger.warning(f"⚠️ Временная ошибка {provider_name}: {e}")
                last_error = e
                self._update_stats(provider_name, success=False)
                continue
                
            except Exception as e:
                # Неожиданные ошибки
                logger.exception(f"💥 Неожиданная ошибка {provider_name}: {e}")
                last_error = AIProviderError(f"Неожиданная ошибка: {e}", provider_name)
                self._update_stats(provider_name, success=False)
                continue
        
        # Все провайдеры не сработали
        self._stats["requests_failed"] += 1
        
        if last_error:
            raise last_error
        else:
            raise AIProviderError(
                "Все AI провайдеры недоступны",
                "manager",
                "all_providers_failed"
            )
    
    async def generate_simple_response(self, user_message: str) -> AIResponse:
        """
        Упрощенный метод для генерации ответа на одно сообщение.
        
        Args:
            user_message: Сообщение пользователя
        
        Returns:
            AIResponse: Ответ от AI провайдера
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
    
    def _update_stats(self, provider_name: str, success: bool) -> None:
        """Обновление статистики провайдера."""
        if provider_name not in self._stats["provider_stats"]:
            self._stats["provider_stats"][provider_name] = {
                "requests": 0,
                "successes": 0,
                "failures": 0,
            }
        
        stats = self._stats["provider_stats"][provider_name]
        stats["requests"] += 1
        
        if success:
            stats["successes"] += 1
        else:
            stats["failures"] += 1
    
    def get_stats(self) -> dict[str, Any]:
        """Получение статистики работы менеджера."""
        return self._stats.copy()
    
    def clear_cache(self) -> None:
        """Очистка кеша ответов."""
        self._cache.clear()
    
    async def health_check(self) -> dict[str, Any]:
        """Проверка здоровья всех провайдеров."""
        results = {
            "manager_status": "healthy",
            "providers": {},
            "statistics": self.get_stats(),
        }
        
        for name, provider in self._providers.items():
            try:
                health = await provider.health_check()
                results["providers"][name] = health
            except Exception as e:
                results["providers"][name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "provider": name,
                }
        
        # Определяем общий статус
        healthy_providers = sum(
            1 for p in results["providers"].values() 
            if p.get("status") == "healthy"
        )
        
        if healthy_providers == 0:
            results["manager_status"] = "unhealthy"
        elif healthy_providers < len(self._providers):
            results["manager_status"] = "degraded"
        
        return results
    
    async def close(self) -> None:
        """Закрытие всех провайдеров."""
        for name, provider in self._providers.items():
            try:
                await provider.close()
                logger.info(f"🔌 Провайдер {name} закрыт")
            except Exception as e:
                logger.error(f"❌ Ошибка закрытия провайдера {name}: {e}")
        
        self._providers.clear()
        logger.info("🔌 AI менеджер закрыт")


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
    "ResponseCache",
    "AIManager",
    "get_ai_manager",
    "close_ai_manager",
    # Повторный экспорт из ai_providers для удобства
    "AIResponse",
    "ConversationMessage",
    "AIProviderError",
]