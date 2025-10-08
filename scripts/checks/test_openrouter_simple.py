#!/usr/bin/env python3
"""
@file: test_openrouter_simple.py
@description: Простой тестовый скрипт для проверки OpenRouter API
@created: 2025-10-07
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Добавляем корневую папку проекта в Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.config import AppConfig, get_config
from app.services.ai_providers.base import ConversationMessage
from app.services.ai_providers.openrouter import OpenRouterProvider

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


class SimpleOpenRouterTest:
    """Простой тест для OpenRouter API."""

    def __init__(self, api_key: str) -> None:
        """Инициализация теста с API ключом."""
        self.api_key = api_key
        self.provider = OpenRouterProvider()

    async def test_simple_request(self, prompt: str) -> bool:
        """Тест простого запроса к OpenRouter API."""
        logger.info("🚀 Начинаем тест OpenRouter API...")
        logger.info("📝 Запрос: %s", prompt)

        try:
            # Создаем временную конфигурацию с переданным API ключом
            config = get_config()
            config.openrouter.openrouter_api_key = self.api_key

            # Проверяем настройку провайдера
            if not self.provider.is_configured():
                logger.error("❌ OpenRouter не настроен правильно")
                return False

            # Создаем сообщения для теста
            messages = [
                ConversationMessage(
                    role="user",
                    content=prompt,
                ),
            ]

            # Отправляем запрос
            logger.info("📡 Отправка запроса к OpenRouter...")
            response = await self.provider.generate_response(messages=messages)

            # Выводим результат
            logger.info("✅ Запрос успешен!")
            logger.info("🤖 Ответ: %s", response.content)
            logger.info("📊 Модель: %s", response.model)
            logger.info("⏱️ Время ответа: %.2fс", response.response_time)
            logger.info("🎯 Токенов использовано: %s", response.tokens_used)

            return True

        except Exception:
            logger.exception("❌ Ошибка при запросе к OpenRouter")
            return False

        finally:
            # Закрываем провайдер
            await self.provider.close()


async def main() -> None:
    """Основная функция теста."""
    logger.info("🧪 Простой тест OpenRouter API")
    logger.info("=" * 50)

    # Получаем API ключ от пользователя
    api_key = input("Введите ваш OpenRouter API ключ: ").strip()
    if not api_key:
        logger.error("❌ API ключ не может быть пустым")
        return

    # Создаем тестовый экземпляр
    tester = SimpleOpenRouterTest(api_key)

    # Получаем запрос от пользователя
    prompt = input("Введите ваш запрос (или нажмите Enter для стандартного): ").strip()
    if not prompt:
        prompt = "Привет! Расскажи кратко о себе в 1-2 предложениях."

    # Выполняем тест
    success = await tester.test_simple_request(prompt)

    logger.info("=" * 50)

    if success:
        logger.info("🎉 Тест завершен успешно!")
        logger.info("✅ OpenRouter API работает корректно")
    else:
        logger.error("😞 Тест завершился с ошибками")
        logger.info("📋 Проверьте ваш API ключ и подключение к интернету")


if __name__ == "__main__":
    asyncio.run(main())
