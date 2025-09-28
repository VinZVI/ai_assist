"""
@file: check_deepseek_api.py
@description: Скрипт для диагностики проблем с DeepSeek API  # noqa: RUF002
@created: 2025-09-20
"""

import sys
from pathlib import Path

# Добавляем корневую папку проекта в Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import httpx
from loguru import logger

from app.config import get_config

# Настройка логирования
logger.remove()
logger.add(
    sys.stdout,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    level="INFO",
)


async def check_api_access() -> bool | None:
    """Проверка доступности API DeepSeek."""
    logger.info("🔍 Проверяем доступность DeepSeek API...")

    config = get_config()

    if not config.deepseek.deepseek_api_key:
        logger.error("❌ DEEPSEEK_API_KEY не установлен")
        return False

    # Проверяем подключение к API
    async with httpx.AsyncClient(
        base_url=config.deepseek.deepseek_base_url,
        headers={
            "Authorization": f"Bearer {config.deepseek.deepseek_api_key}",
            "Content-Type": "application/json",
        },
        timeout=httpx.Timeout(10.0),
    ) as client:
        try:
            response = await client.post(
                "/chat/completions",
                json={
                    "model": config.deepseek.deepseek_model,
                    "messages": [
                        {"role": "user", "content": "Привет! Это тестовое сообщение."}
                    ],
                    "max_tokens": 10,
                },
            )

            if response.status_code == 200:
                logger.info("✅ DeepSeek API доступен")
                data = response.json()
                logger.info(f"🤖 Ответ: {data['choices'][0]['message']['content']}")
                return True
            if response.status_code == 401:
                logger.error("❌ Неверный API ключ")
                logger.info("📋 Проверьте настройки в .env файле")
                return False
            if response.status_code == 429:
                logger.warning("⚠️ Превышен лимит запросов")
                return True  # API доступен, но лимит превышен
            logger.error(f"❌ Ошибка API: {response.status_code} - {response.text}")
            return False

        except httpx.TimeoutException:
            logger.error("⏰ Таймаут при подключении к DeepSeek API")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка при подключении к DeepSeek API: {e}")
            return False


async def check_balance_info() -> bool:
    """Дополнительная проверка информации о балансе (если доступно)."""
    logger.info("💳 Проверяем информацию о балансе...")

    config = get_config()

    try:
        async with httpx.AsyncClient(
            base_url=config.deepseek.deepseek_base_url,
            headers={
                "Authorization": f"Bearer {config.deepseek.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(10.0),
        ) as client:
            # Попробуем получить информацию о балансе
            try:
                balance_response = await client.get("/dashboard/billing/credit_grants")

                if balance_response.status_code == 200:
                    balance_data = balance_response.json()
                    logger.info(f"💰 Информация о подписке: {balance_data}")
                    return True
            except:
                logger.info("ℹ️ Информация о балансе недоступна через API")

    except Exception as e:
        logger.warning(f"⚠️ Не удалось получить информацию о балансе: {e}")

    return False


async def main() -> None:
    """Основная функция диагностики."""
    logger.info("🚀 Начинаем диагностику DeepSeek API")

    # Проверяем конфигурацию
    try:
        get_config()
        logger.info("✅ Конфигурация загружена успешно")
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки конфигурации: {e}")
        logger.info("📋 Проверьте настройки в .env файле")
        return

    # Проверяем доступность API
    api_available = await check_api_access()

    if api_available:
        logger.info("✅ DeepSeek API готов к работе")
    else:
        logger.error("😞 Обнаружены проблемы с DeepSeek API")
        logger.info("📋 Рекомендации:")
        logger.info("   1. Проверьте настройки в .env файле")
        logger.info("   2. Убедитесь, что API ключ действителен")
        logger.info("   3. Проверьте подключение к интернету")
        logger.info("   4. Убедитесь, что у вас есть доступ к DeepSeek API")


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Диагностика прервана пользователем")
    except Exception as e:
        logger.error(f"💥 Непредвиденная ошибка: {e}")
