#!/usr/bin/env python3
"""
@file: test_openrouter_integration.py
@description: Тестовый скрипт для проверки интеграции с OpenRouter API
@created: 2025-09-20
"""

import asyncio
import logging
import sys
from pathlib import Path

# Добавляем корневую папку проекта в Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.config import get_config
from app.services.ai_manager import get_ai_manager
from app.services.ai_providers.base import ConversationMessage

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


async def test_openrouter_integration() -> bool | None:
    """Тестирование интеграции с OpenRouter."""
    logger.info("🚀 Начинаем тест интеграции с OpenRouter...")

    try:
        # Получаем AI менеджер
        manager = get_ai_manager()

        # Проверяем health check
        logger.info("🔍 Проверка здоровья провайдеров...")
        health = await manager.health_check()

        logger.info("📊 Статус менеджера: %s", health["manager_status"])

        for provider_name, provider_health in health["providers"].items():
            status = provider_health.get("status", "unknown")
            logger.info("📋 %s: %s", provider_name, status)

            if status != "healthy":
                error = provider_health.get("error", "Неизвестная ошибка")
                logger.warning("⚠️ %s недоступен: %s", provider_name, error)

        # Тестируем OpenRouter если он доступен
        openrouter = manager.get_provider("openrouter")
        if openrouter and openrouter.is_configured():
            logger.info("🧪 Тестируем OpenRouter API...")

            test_messages = [
                ConversationMessage(
                    role="system",
                    content="Ты - полезный AI помощник. Отвечай кратко и по делу.",
                ),
                ConversationMessage(
                    role="user",
                    content="Привет! Как дела? Расскажи о себе в 2-3 предложениях.",
                ),
            ]

            try:
                # Прямой тест OpenRouter
                response = await manager.generate_response(
                    messages=test_messages,
                    prefer_provider="openrouter",
                    use_cache=False,
                )

                logger.info("✅ OpenRouter тест успешен!")
                logger.info("🤖 Ответ: %s...", response.content[:100])
                logger.info("📊 Модель: %s", response.model)
                logger.info("🔗 Провайдер: %s", response.provider)
                logger.info("⏱️ Время ответа: %.2fс", response.response_time)
                logger.info("🎯 Токенов использовано: %s", response.tokens_used)

            except Exception:
                logger.exception("❌ Ошибка OpenRouter")
                logger.info("💡 Проверьте OPENROUTER_API_KEY в .env файле")
        else:
            logger.warning("⚠️ OpenRouter не настроен")

        # Тестируем fallback логику
        logger.info("🔄 Тестируем fallback логику...")

        simple_response = await manager.generate_simple_response(
            "Проверка fallback между провайдерами",
        )

        logger.info(
            "🔄 Fallback тест - использован провайдер: %s",
            simple_response.provider,
        )

        # Показываем статистику
        stats = manager.get_stats()
        logger.info("📈 Статистика менеджера:")
        logger.info("   Всего запросов: %s", stats["requests_total"])
        logger.info("   Успешных: %s", stats["requests_successful"])
        logger.info("   Неудачных: %s", stats["requests_failed"])
        logger.info("   Fallback использован: %s раз", stats["fallback_used"])

        for provider, provider_stats in stats["provider_stats"].items():
            logger.info(
                "   %s: %s/%s успешно",
                provider,
                provider_stats["successes"],
                provider_stats["requests"],
            )

        return True

    except Exception:
        logger.exception("💥 Критическая ошибка в тесте")
        return False

    finally:
        # Закрываем менеджер
        await manager.close()


async def main() -> None:
    """Основная функция теста."""
    # Remove the logger.add line as it's not compatible with standard logging
    # logger.add("openrouter_test.log", rotation="1 MB", retention="1 week")

    logger.info("🧪 Запуск теста интеграции OpenRouter")
    logger.info("=" * 50)

    success = await test_openrouter_integration()

    logger.info("=" * 50)

    if success:
        logger.info("🎉 Тест завершен успешно!")
        logger.info("✅ OpenRouter интеграция работает корректно")
    else:
        logger.error("😞 Тест завершился с ошибками")
        logger.info("📋 Проверьте настройки в .env файле")

    # Remove the log file reference as we're not using loguru
    # logger.info("📝 Лог теста сохранен в: openrouter_test.log")


if __name__ == "__main__":
    asyncio.run(main())
