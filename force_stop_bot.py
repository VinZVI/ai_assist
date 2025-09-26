#!/usr/bin/env python3
"""
@file: force_stop_bot.py
@description: Принудительная остановка бота и очистка всех процессов
@created: 2025-09-20
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

# Добавляем корневую папку проекта в PATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import httpx
from loguru import logger

from app.config import get_config


def kill_python_processes():
    """Принудительное завершение всех процессов Python."""
    logger.info("🔪 Принудительное завершение всех процессов Python...")

    try:
        # Windows команда для завершения процессов Python
        result = subprocess.run(
            ["taskkill", "/F", "/IM", "python.exe"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            logger.success("✅ Все процессы Python завершены")
        else:
            logger.warning(f"⚠️ Команда taskkill вернула код: {result.returncode}")
            logger.info(f"Вывод: {result.stdout}")

    except subprocess.TimeoutExpired:
        logger.error("❌ Timeout при выполнении taskkill")
    except Exception as e:
        logger.error(f"❌ Ошибка при завершении процессов: {e}")


async def clear_webhook_completely():
    """Полная очистка webhook с несколькими попытками."""
    logger.info("🧹 Полная очистка webhook...")

    try:
        config = get_config()

        if not config.telegram or not config.telegram.bot_token:
            logger.error("❌ Токен бота не настроен!")
            return False

        bot_token = config.telegram.bot_token

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Многократная очистка webhook
            for attempt in range(3):
                logger.info(f"🗑️ Попытка очистки webhook #{attempt + 1}")

                delete_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"

                try:
                    response = await client.post(
                        delete_url,
                        json={
                            "drop_pending_updates": True,
                        },
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if data.get("ok"):
                            logger.success(f"✅ Webhook очищен (попытка {attempt + 1})")
                        else:
                            logger.warning(f"⚠️ API ответил: {data}")
                    else:
                        logger.warning(f"⚠️ HTTP статус: {response.status_code}")

                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при попытке {attempt + 1}: {e}")

                # Пауза между попытками
                if attempt < 2:
                    await asyncio.sleep(2)

            # Проверяем результат
            try:
                info_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
                info_response = await client.get(info_url)

                if info_response.status_code == 200:
                    info_data = info_response.json()
                    if info_data.get("ok"):
                        webhook_url = info_data.get("result", {}).get("url", "")
                        pending_updates = info_data.get("result", {}).get(
                            "pending_update_count",
                            0,
                        )

                        logger.info(
                            f"📊 Финальный статус webhook: {webhook_url or 'очищен'}",
                        )
                        logger.info(f"📊 Ожидающих обновлений: {pending_updates}")

                        return not webhook_url  # True если webhook очищен

            except Exception as e:
                logger.warning(f"⚠️ Не удалось проверить статус webhook: {e}")

    except Exception as e:
        logger.error(f"❌ Ошибка при очистке webhook: {e}")

    return False


def wait_for_system_stabilization():
    """Ожидание стабилизации системы."""
    logger.info("⏳ Ожидание стабилизации системы (60 секунд)...")

    for i in range(60, 0, -10):
        logger.info(f"⏰ Осталось {i} секунд...")
        time.sleep(10)

    logger.info("✅ Ожидание завершено")


async def test_bot_readiness():
    """Тест готовности бота к запуску."""
    logger.info("🧪 Тестирование готовности бота...")

    try:
        config = get_config()

        if not config.telegram or not config.telegram.bot_token:
            logger.error("❌ Токен бота не настроен!")
            return False

        bot_token = config.telegram.bot_token

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Простой тест API
            me_url = f"https://api.telegram.org/bot{bot_token}/getMe"
            response = await client.get(me_url)

            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    bot_info = data.get("result", {})
                    logger.success(
                        f"✅ Бот готов: @{bot_info.get('username', 'unknown')}",
                    )
                    return True

            logger.error(f"❌ Тест API не прошел: {response.status_code}")

    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")

    return False


async def main():
    """Основная функция принудительной остановки."""
    logger.add("force_stop.log", rotation="1 MB", retention="1 week")

    logger.info("🛑 ПРИНУДИТЕЛЬНАЯ ОСТАНОВКА БОТА")
    logger.info("=" * 60)

    # Шаг 1: Завершение всех процессов Python
    kill_python_processes()

    logger.info("=" * 60)

    # Шаг 2: Очистка webhook
    webhook_cleared = await clear_webhook_completely()

    logger.info("=" * 60)

    # Шаг 3: Ожидание стабилизации
    wait_for_system_stabilization()

    logger.info("=" * 60)

    # Шаг 4: Тест готовности
    ready = await test_bot_readiness()

    logger.info("=" * 60)

    if webhook_cleared and ready:
        logger.success("🎉 ВСЁ ГОТОВО!")
        logger.info("✅ Webhook очищен")
        logger.info("✅ Система стабилизировалась")
        logger.info("✅ Бот готов к запуску")
        logger.info("")
        logger.info("💡 Теперь можно запустить бота:")
        logger.info("   uv run python main.py")
    else:
        logger.error("😞 Не все проблемы решены")
        logger.info("💡 Рекомендации:")
        if not webhook_cleared:
            logger.info("   - Webhook может быть не полностью очищен")
        if not ready:
            logger.info("   - Проверьте токен бота и подключение к интернету")
        logger.info("   - Попробуйте повторить через несколько минут")
        logger.info("   - Перезагрузите компьютер в крайнем случае")


if __name__ == "__main__":
    asyncio.run(main())
