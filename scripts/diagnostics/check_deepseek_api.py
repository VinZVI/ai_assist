#!/usr/bin/env python3
"""
@file: check_deepseek_api.py
@description: Скрипт для диагностики проблем с DeepSeek API
@created: 2025-09-20
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую папку проекта в PATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import httpx
from loguru import logger

from app.config import get_config


async def check_deepseek_api_status():
    """Проверка статуса DeepSeek API и диагностика проблем."""
    logger.info("🔍 Начинаем диагностику DeepSeek API...")

    try:
        config = get_config()

        # Проверяем конфигурацию
        logger.info("📋 Проверяем конфигурацию...")

        if not config.deepseek.deepseek_api_key:
            logger.error("❌ API ключ DeepSeek не настроен!")
            return None

        if config.deepseek.deepseek_api_key.startswith("your_"):
            logger.error("❌ API ключ DeepSeek не заменен на реальный!")
            return None

        logger.info(
            f"✅ API ключ: {'*' * 20}...{config.deepseek.deepseek_api_key[-8:]}",
        )
        logger.info(f"✅ Base URL: {config.deepseek.deepseek_base_url}")
        logger.info(f"✅ Модель: {config.deepseek.deepseek_model}")

        # Проверяем подключение к API
        logger.info("🌐 Проверяем подключение к DeepSeek API...")

        headers = {
            "Authorization": f"Bearer {config.deepseek.deepseek_api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AI-Assistant-Bot/1.0",
        }

        timeout = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)

        async with httpx.AsyncClient(
            base_url=config.deepseek.deepseek_base_url,
            headers=headers,
            timeout=timeout,
        ) as client:
            # Простой тестовый запрос
            test_payload = {
                "model": config.deepseek.deepseek_model,
                "messages": [
                    {"role": "user", "content": "Hello, this is a test."},
                ],
                "max_tokens": 10,
                "temperature": 0.1,
            }

            logger.info("📡 Отправляем тестовый запрос...")

            response = await client.post("/v1/chat/completions", json=test_payload)

            logger.info(f"📊 Статус ответа: {response.status_code}")

            if response.status_code == 200:
                logger.success("✅ API работает корректно!")
                data = response.json()

                if data.get("choices"):
                    content = data["choices"][0].get("message", {}).get("content", "")
                    logger.info(f"🤖 Тестовый ответ: {content}")

                if "usage" in data:
                    usage = data["usage"]
                    logger.info(f"📈 Использование токенов: {usage}")

                return True

            if response.status_code == 401:
                logger.error("❌ Ошибка 401: Неверный API ключ!")
                logger.info("💡 Проверьте правильность API ключа в .env файле")

            elif response.status_code == 402:
                logger.error("❌ Ошибка 402: Недостаточно средств на счете!")
                logger.info("💡 Решение проблемы:")
                logger.info(
                    "   1. Войдите в личный кабинет DeepSeek: https://platform.deepseek.com/",
                )
                logger.info("   2. Проверьте баланс на странице Billing")
                logger.info("   3. Пополните счет если необходимо")
                logger.info("   4. Проверьте лимиты использования API")

            elif response.status_code == 429:
                logger.error("❌ Ошибка 429: Превышен лимит запросов!")
                logger.info("💡 Подождите несколько минут и попробуйте снова")

            elif response.status_code >= 500:
                logger.error(f"❌ Ошибка сервера DeepSeek: {response.status_code}")
                logger.info("💡 Попробуйте повторить запрос позже")

            else:
                logger.error(f"❌ Неизвестная ошибка: {response.status_code}")

            # Показываем тело ответа для диагностики
            try:
                error_data = response.json()
                logger.info(f"📄 Детали ошибки: {error_data}")
            except:
                logger.info(f"📄 Тело ответа: {response.text}")

            return False

    except httpx.ConnectError as e:
        logger.error(f"❌ Ошибка подключения: {e}")
        logger.info("💡 Проверьте интернет соединение и URL сервиса")
        return False

    except httpx.TimeoutException:
        logger.error("❌ Timeout при подключении к API")
        logger.info("💡 Попробуйте увеличить timeout или повторить позже")
        return False

    except Exception as e:
        logger.exception(f"💥 Неожиданная ошибка: {e}")
        return False


async def check_balance_info():
    """Дополнительная проверка информации о балансе (если доступно)."""
    logger.info("💳 Проверяем информацию о балансе...")

    try:
        config = get_config()

        headers = {
            "Authorization": f"Bearer {config.deepseek.deepseek_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(
            base_url=config.deepseek.deepseek_base_url,
            headers=headers,
            timeout=httpx.Timeout(10.0),
        ) as client:
            # Попробуем получить информацию о балансе
            try:
                balance_response = await client.get(
                    "/v1/dashboard/billing/subscription",
                )
                if balance_response.status_code == 200:
                    balance_data = balance_response.json()
                    logger.info(f"💰 Информация о подписке: {balance_data}")
                    return True
            except:
                logger.info("ℹ️ Информация о балансе недоступна через API")

    except Exception as e:
        logger.warning(f"⚠️ Не удалось получить информацию о балансе: {e}")

    return False


async def main():
    """Основная функция диагностики."""
    logger.add("deepseek_diagnosis.log", rotation="1 MB", retention="1 week")

    logger.info("🚀 Запуск диагностики DeepSeek API")
    logger.info("=" * 50)

    # Основная проверка API
    api_status = await check_deepseek_api_status()

    logger.info("=" * 50)

    # Дополнительная проверка баланса
    await check_balance_info()

    logger.info("=" * 50)

    if api_status:
        logger.success("🎉 Диагностика завершена успешно!")
        logger.info("✅ DeepSeek API готов к работе")
    else:
        logger.error("😞 Обнаружены проблемы с DeepSeek API")
        logger.info("📋 Рекомендации:")
        logger.info("   1. Проверьте настройки в .env файле")
        logger.info("   2. Убедитесь в правильности API ключа")
        logger.info("   3. Проверьте баланс в личном кабинете DeepSeek")
        logger.info("   4. Обратитесь в поддержку DeepSeek если проблема не решается")

    logger.info("📝 Лог диагностики сохранен в: deepseek_diagnosis.log")


if __name__ == "__main__":
    asyncio.run(main())
