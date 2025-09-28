#!/usr/bin/env python3
"""
@file: clear_webhook.py
@description: Инструмент для очистки webhook и решения конфликтов бота
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


async def clear_webhook() -> bool:
    """Очистка webhook для решения конфликтов."""
    logger.info("🔧 Начинаем очистку webhook...")

    try:
        config = get_config()

        if not config.telegram or not config.telegram.bot_token:
            logger.error("❌ Токен бота не настроен!")
            return False

        bot_token = config.telegram.bot_token
        logger.info(f"🤖 Работаем с ботом: ...{bot_token[-10:]}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Получаем текущую информацию о webhook
            info_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
            logger.info("📋 Получаем информацию о текущем webhook...")

            info_response = await client.get(info_url)
            if info_response.status_code == 200:
                info_data = info_response.json()
                if info_data.get("ok"):
                    webhook_info = info_data.get("result", {})
                    current_url = webhook_info.get("url", "")
                    pending_updates = webhook_info.get("pending_update_count", 0)

                    logger.info(
                        f"📊 Текущий webhook URL: {current_url or 'не установлен'}",
                    )
                    logger.info(f"📊 Ожидающих обновлений: {pending_updates}")

                    if not current_url:
                        logger.info("✅ Webhook уже очищен")
                        return True
                else:
                    logger.error(f"❌ Ошибка получения webhook info: {info_data}")

            # Очищаем webhook
            delete_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
            logger.info("🗑️ Очищаем webhook...")

            delete_response = await client.post(
                delete_url,
                json={"drop_pending_updates": True},
            )

            if delete_response.status_code == 200:
                delete_data = delete_response.json()
                if delete_data.get("ok"):
                    logger.success("✅ Webhook успешно очищен!")

                    # Проверяем результат
                    check_response = await client.get(info_url)
                    if check_response.status_code == 200:
                        check_data = check_response.json()
                        if check_data.get("ok"):
                            final_url = check_data.get("result", {}).get("url", "")
                            if not final_url:
                                logger.success("🎉 Webhook полностью удален!")
                                return True
                            logger.warning(f"⚠️ Webhook все еще установлен: {final_url}")
                else:
                    logger.error(f"❌ Ошибка удаления webhook: {delete_data}")
            else:
                logger.error(
                    f"❌ HTTP ошибка при удалении webhook: "
                    f"{delete_response.status_code}",
                )

    except httpx.TimeoutException:
        logger.error("❌ Timeout при обращении к Telegram API")
    except Exception as e:
        logger.exception(f"💥 Неожиданная ошибка: {e}")

    return False


async def wait_for_conflict_resolution() -> None:
    """Ожидание разрешения конфликта."""
    logger.info("⏳ Ждем разрешения конфликта (30 секунд)...")
    await asyncio.sleep(30)
    logger.info("✅ Ожидание завершено")


async def main() -> None:
    """Основная функция."""
    logger.add("webhook_clear.log", rotation="1 MB", retention="1 week")

    logger.info("🚀 Инструмент очистки webhook")
    logger.info("=" * 50)

    # Очищаем webhook
    success = await clear_webhook()

    if success:
        logger.info("=" * 50)
        await wait_for_conflict_resolution()
        logger.info("=" * 50)
        logger.success("🎉 Готово! Попробуйте запустить бота снова")
        logger.info("💡 Выполните: uv run python main.py")
    else:
        logger.error("😞 Не удалось очистить webhook")
        logger.info("💡 Рекомендации:")
        logger.info("   1. Проверьте токен бота в .env")
        logger.info("   2. Убедитесь в доступности Telegram API")
        logger.info("   3. Попробуйте повторить через несколько минут")


if __name__ == "__main__":
    asyncio.run(main())
