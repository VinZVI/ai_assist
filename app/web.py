"""
@file: web.py
@description: Веб-сервер для healthcheck и webhook endpoint
@dependencies: fastapi, uvicorn, loguru
@created: 2025-10-05
"""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import get_config
from app.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    """Lifespan manager for the FastAPI application."""
    logger.info("🚀 Запуск веб-сервера...")

    # Инициализация базы данных
    try:
        await init_db()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации базы данных: {e}")
        raise

    yield

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
    Healthcheck endpoint.

    Returns:
        JSONResponse: Статус здоровья приложения
    """
    try:
        # Проверяем конфигурацию
        config = get_config()
        if not config:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "error", "message": "Конфигурация не загружена"},
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ok", "message": "Приложение работает нормально"},
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "message": f"Ошибка healthcheck: {e}"},
        )


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
