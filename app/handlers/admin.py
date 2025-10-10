"""
@file: handlers/admin.py
@description: Обработчик админских команд
@dependencies: aiogram, loguru
@created: 2025-10-10
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from app.config import get_config
from app.database import get_session
from app.lexicon.gettext import get_log_text
from app.services.ai_manager import get_ai_manager

# Создаем роутер для обработчиков админских команд
admin_router = Router(name="admin")


@admin_router.message(Command("health"))
async def admin_health_check(message: Message) -> None:
    """
    Админская команда /health с расширенной информацией.

    Args:
        message: Объект сообщения от пользователя
    """
    try:
        # Проверяем, что у сообщения есть информация о пользователе
        if not message.from_user:
            logger.warning(
                get_log_text("admin.unauthorized_access").format(
                    user_id="unknown", command="/health"
                )
            )
            return

        # Проверяем, что пользователь является администратором
        config = get_config()
        # Получаем админские ID из конфигурации
        admin_ids = config.telegram.get_admin_ids()

        if message.from_user.id not in admin_ids:
            logger.warning(
                get_log_text("admin.unauthorized_access").format(
                    user_id=message.from_user.id, command="/health"
                )
            )
            return

        # Логируем попытку админского health check
        logger.info(
            get_log_text("admin.health_check_requested").format(
                admin_id=message.from_user.id
            )
        )

        # Проверяем конфигурацию
        config_status = "healthy" if config else "unhealthy"

        # Проверяем подключение к базе данных
        db_status = "unknown"
        try:
            async with get_session() as session:
                await session.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {e!s}"

        # Проверяем AI провайдеры
        ai_manager = get_ai_manager()
        ai_health = await ai_manager.health_check()
        ai_status = ai_health["manager_status"]

        # Формируем детализированный отчет
        health_report = f"""📊 <b>Расширенный Health Check</b>

<b>Конфигурация:</b> {config_status}
<b>База данных:</b> {db_status}
<b>AI Провайдеры:</b> {ai_status}

<b>Детали AI провайдеров:</b>
"""

        for provider_name, provider_health in ai_health["providers"].items():
            status = provider_health.get("status", "unknown")
            error = provider_health.get("error", "")
            health_report += f"• {provider_name}: {status}"
            if error:
                health_report += f" ({error})"
            health_report += "\n"

        # Отправляем детализированный отчет
        await message.answer(health_report, parse_mode="HTML")
        logger.info(get_log_text("admin.health_check_completed"))

    except Exception as e:
        logger.error(
            get_log_text("admin.health_check_error").format(
                admin_id=message.from_user.id if message.from_user else "unknown",
                error=str(e),
            )
        )
        await message.answer(f"❌ Ошибка healthcheck: {e}")
