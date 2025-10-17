"""
@file: web.py
@description: Веб-сервер для healthcheck и webhook endpoint
@dependencies: fastapi, uvicorn, loguru
@created: 2025-10-05
@updated: 2025-10-15
"""

import asyncio
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import psutil
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import get_config
from app.database import check_connection, close_db, init_db
from app.middleware.anti_spam import AntiSpamMiddleware
from app.middleware.content_filter import ContentFilterMiddleware
from app.middleware.emotional_profiling import EmotionalProfilingMiddleware
from app.middleware.message_counter import MessageCountingMiddleware
from app.middleware.metrics import MetricsMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.services.ai_manager import get_ai_manager
from app.services.analytics import analytics_service
from app.services.monitoring import monitoring_service

# Global variables for metrics
_request_count = 0
_error_count = 0
_start_time = asyncio.get_event_loop().time()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    """Lifespan manager for the FastAPI application."""
    global _start_time
    _start_time = asyncio.get_event_loop().time()

    logger.info("🚀 Запуск веб-сервера...")

    # Инициализация базы данных
    try:
        await init_db()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации базы данных: {e}")
        raise

    # Запуск сервисов мониторинга и аналитики
    try:
        await monitoring_service.start_monitoring()
        await analytics_service.start_analytics_collection()
        logger.info("✅ Сервисы мониторинга и аналитики запущены")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска сервисов мониторинга: {e}")

    yield

    # Остановка сервисов мониторинга и аналитики
    try:
        await monitoring_service.stop_monitoring()
        await analytics_service.stop_analytics_collection()
        logger.info("✅ Сервисы мониторинга и аналитики остановлены")
    except Exception as e:
        logger.error(f"❌ Ошибка остановки сервисов мониторинга: {e}")

    # Закрытие подключения к базе данных
    try:
        await close_db()
        logger.info("✅ Подключение к базе данных закрыто")
    except Exception as e:
        logger.error(f"❌ Ошибка закрытия подключения к базе данных: {e}")


# Создаем FastAPI приложение
app = FastAPI(
    title="AI-Компаньон API",
    description="API для Telegram бота AI-Компаньон",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> JSONResponse:
    """
    Healthcheck endpoint with detailed system metrics.

    Returns:
        JSONResponse: Detailed status of the application
    """
    try:
        # Проверяем конфигурацию
        config = get_config()
        if not config:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "error",
                    "message": "Конфигурация не загружена",
                    "timestamp": time.time(),
                    "components": {
                        "config": "error",
                        "database": "unknown",
                        "ai_providers": "unknown",
                    },
                },
            )

        # Проверяем подключение к базе данных
        db_status = await check_connection()
        db_status_str = "healthy" if db_status else "unhealthy"

        # Проверяем AI провайдеры
        ai_manager = get_ai_manager()
        ai_health = await ai_manager.health_check()
        ai_status = ai_health["manager_status"]

        # Получаем статистику middleware
        anti_spam_stats = AntiSpamMiddleware.get_anti_spam_stats()
        content_filter_stats = ContentFilterMiddleware.get_content_filter_stats()
        # emotional_stats = {}  # Placeholder for emotional profiling stats (removed as unused)
        message_count_stats = MessageCountingMiddleware.get_message_count_stats()
        metrics_stats = MetricsMiddleware.get_metrics_stats()
        rate_limit_stats = RateLimitMiddleware.get_rate_limit_stats()

        # Получаем системные метрики
        system_metrics = _get_system_metrics()

        # Формируем общий статус
        overall_status = "healthy"
        if not db_status or ai_status != "healthy":
            overall_status = "degraded"

        # Вычисляем uptime
        uptime = asyncio.get_event_loop().time() - _start_time

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": overall_status,
                "message": "Приложение работает нормально",
                "timestamp": time.time(),
                "uptime_seconds": uptime,
                "components": {
                    "config": "healthy",
                    "database": db_status_str,
                    "ai_providers": ai_status,
                },
                "details": {
                    "ai_providers": ai_health["providers"],
                    "middleware_stats": {
                        "anti_spam": anti_spam_stats,
                        "content_filter": content_filter_stats,
                        "message_counting": message_count_stats,
                        "metrics": metrics_stats,
                        "rate_limit": rate_limit_stats,
                    },
                    "system_metrics": system_metrics,
                },
            },
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "message": f"Ошибка healthcheck: {e}",
                "timestamp": time.time(),
                "components": {
                    "config": "unknown",
                    "database": "unknown",
                    "ai_providers": "unknown",
                },
            },
        )


@app.get("/metrics")
async def metrics_endpoint() -> JSONResponse:
    """
    Metrics endpoint for monitoring and scaling decisions with system metrics.

    Returns:
        JSONResponse: Detailed metrics about the application
    """
    try:
        # Получаем статистику AI менеджера
        ai_manager = get_ai_manager()
        ai_stats = ai_manager.get_stats()

        # Получаем статистику middleware
        anti_spam_stats = AntiSpamMiddleware.get_anti_spam_stats()
        content_filter_stats = ContentFilterMiddleware.get_content_filter_stats()
        message_count_stats = MessageCountingMiddleware.get_message_count_stats()
        metrics_stats = MetricsMiddleware.get_metrics_stats()
        rate_limit_stats = RateLimitMiddleware.get_rate_limit_stats()

        # Получаем системные метрики
        system_metrics = _get_system_metrics()

        # Вычисляем uptime
        uptime = asyncio.get_event_loop().time() - _start_time

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "timestamp": time.time(),
                "uptime_seconds": uptime,
                "ai_stats": ai_stats,
                "middleware_stats": {
                    "anti_spam": anti_spam_stats,
                    "content_filter": content_filter_stats,
                    "message_counting": message_count_stats,
                    "metrics": metrics_stats,
                    "rate_limit": rate_limit_stats,
                },
                "system_metrics": system_metrics,
            },
        )
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": f"Ошибка получения метрик: {e}",
                "timestamp": time.time(),
            },
        )


@app.get("/analytics")
async def analytics_endpoint(hours: int = 24) -> JSONResponse:
    """
    Analytics endpoint for detailed performance insights.

    Args:
        hours: Период анализа в часах

    Returns:
        JSONResponse: Detailed analytics report
    """
    try:
        # Собираем аналитику
        analytics_data = await analytics_service.collect_analytics()

        # Получаем отчет
        analytics_report = analytics_service.get_analytics_report(hours)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "timestamp": time.time(),
                "analytics_data": analytics_data,
                "analytics_report": analytics_report,
            },
        )
    except Exception as e:
        logger.error(f"Analytics endpoint failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": f"Ошибка получения аналитики: {e}",
                "timestamp": time.time(),
            },
        )


@app.get("/analytics/report")
async def analytics_report_endpoint(hours: int = 24) -> JSONResponse:
    """
    Analytics report endpoint for business insights.

    Args:
        hours: Период анализа в часах

    Returns:
        JSONResponse: Analytics report
    """
    try:
        # Получаем отчет
        analytics_report = analytics_service.get_analytics_report(hours)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "timestamp": time.time(),
                "report": analytics_report,
            },
        )
    except Exception as e:
        logger.error(f"Analytics report endpoint failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": f"Ошибка получения отчета: {e}",
                "timestamp": time.time(),
            },
        )


def _get_system_metrics() -> dict[str, Any]:
    """
    Получение системных метрик для мониторинга производительности.

    Returns:
        dict: Системные метрики
    """
    try:
        # Получаем метрики CPU
        cpu_percent = psutil.cpu_percent(interval=1)

        # Получаем метрики памяти
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available = memory.available
        memory_total = memory.total

        # Получаем метрики диска
        disk = psutil.disk_usage("/")
        disk_percent = (disk.used / disk.total) * 100
        disk_free = disk.free
        disk_total = disk.total

        # Получаем метрики сети
        net_io = psutil.net_io_counters()
        bytes_sent = net_io.bytes_sent
        bytes_recv = net_io.bytes_recv

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "memory_available_bytes": memory_available,
            "memory_total_bytes": memory_total,
            "disk_percent": disk_percent,
            "disk_free_bytes": disk_free,
            "disk_total_bytes": disk_total,
            "network_bytes_sent": bytes_sent,
            "network_bytes_received": bytes_recv,
        }
    except Exception as e:
        logger.warning(f"Ошибка получения системных метрик: {e}")
        return {"error": f"Не удалось получить системные метрики: {e}"}


@app.post("/webhook")
async def telegram_webhook(request: Request) -> Response:  # noqa: ARG001
    """
    Telegram webhook endpoint.

    Args:
        request: HTTP запрос от Telegram

    Returns:
        Response: Пустой ответ
    """
    # Эта функция будет обрабатываться через aiogram
    # Здесь мы просто возвращаем пустой ответ
    return Response(status_code=status.HTTP_200_OK)


@app.get("/")
async def root() -> JSONResponse:
    """
    Root endpoint.

    Returns:
        JSONResponse: Приветственное сообщение
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Добро пожаловать в AI-Компаньон API", "version": "1.0.0"},
    )


if __name__ == "__main__":
    import uvicorn

    config = get_config()

    uvicorn.run(
        "app.web:app",
        host="0.0.0.0",  # noqa: S104
        port=8000,
        reload=config.debug,
        log_level=config.log_level.lower(),
    )
