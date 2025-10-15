"""
@file: services/health_check.py
@description: Сервис проверки здоровья для мониторинга состояния бота
@dependencies: asyncio, loguru, app.config, app.database, app.services.ai_manager
@created: 2025-10-15
"""

import asyncio
import time
from typing import Any, Dict

from loguru import logger

from app.config import get_config
from app.database import check_connection
from app.services.ai_manager import get_ai_manager


class HealthCheckService:
    """Сервис проверки здоровья для мониторинга состояния бота."""

    def __init__(self) -> None:
        """Инициализация сервиса проверки здоровья."""
        self.config = get_config()
        self.last_check_time = 0.0
        self.last_check_result: dict[str, Any] = {}

    async def perform_health_check(self) -> dict[str, Any]:
        """
        Выполнение полной проверки здоровья системы.

        Returns:
            Dict[str, Any]: Результаты проверки здоровья
        """
        logger.info("Начало проверки здоровья системы")

        # Собираем результаты проверки
        health_results = {
            "timestamp": time.time(),
            "status": "unknown",
            "components": {},
            "details": {},
        }

        try:
            # Проверяем конфигурацию
            config_status = self._check_config()
            health_results["components"]["config"] = config_status

            # Проверяем подключение к базе данных
            db_status = await self._check_database()
            health_results["components"]["database"] = db_status

            # Проверяем AI провайдеры
            ai_status = await self._check_ai_providers()
            health_results["components"]["ai_providers"] = ai_status

            # Определяем общий статус
            overall_status = self._determine_overall_status(
                health_results["components"]
            )
            health_results["status"] = overall_status

            logger.info(f"Проверка здоровья завершена. Общий статус: {overall_status}")

        except Exception as e:
            logger.error(f"Ошибка при выполнении проверки здоровья: {e}")
            health_results["status"] = "error"
            health_results["error"] = str(e)

        # Сохраняем результаты для последующего использования
        self.last_check_time = time.time()
        self.last_check_result = health_results

        return health_results

    def _check_config(self) -> dict[str, Any]:
        """
        Проверка конфигурации.

        Returns:
            Dict[str, Any]: Результат проверки конфигурации
        """
        try:
            config = get_config()
            if config:
                return {
                    "status": "healthy",
                    "message": "Конфигурация загружена успешно",
                }
            return {"status": "unhealthy", "message": "Конфигурация не загружена"}
        except Exception as e:
            return {"status": "error", "message": f"Ошибка проверки конфигурации: {e}"}

    async def _check_database(self) -> dict[str, Any]:
        """
        Проверка подключения к базе данных.

        Returns:
            Dict[str, Any]: Результат проверки базы данных
        """
        try:
            db_status = await check_connection()
            if db_status:
                return {
                    "status": "healthy",
                    "message": "Подключение к базе данных установлено",
                }
            return {
                "status": "unhealthy",
                "message": "Нет подключения к базе данных",
            }
        except Exception as e:
            return {"status": "error", "message": f"Ошибка проверки базы данных: {e}"}

    async def _check_ai_providers(self) -> dict[str, Any]:
        """
        Проверка AI провайдеров.

        Returns:
            Dict[str, Any]: Результат проверки AI провайдеров
        """
        try:
            ai_manager = get_ai_manager()
            ai_health = await ai_manager.health_check()

            # Проверяем статус менеджера
            manager_status = ai_health.get("manager_status", "unknown")

            if manager_status == "healthy":
                return {
                    "status": "healthy",
                    "message": "Все AI провайдеры работают нормально",
                    "providers": ai_health.get("providers", {}),
                }
            if manager_status == "degraded":
                return {
                    "status": "degraded",
                    "message": "Некоторые AI провайдеры недоступны",
                    "providers": ai_health.get("providers", {}),
                }
            return {
                "status": "unhealthy",
                "message": "Все AI провайдеры недоступны",
                "providers": ai_health.get("providers", {}),
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка проверки AI провайдеров: {e}",
            }

    def _determine_overall_status(self, components: dict[str, Any]) -> str:
        """
        Определение общего статуса на основе компонентов.

        Args:
            components: Словарь с результатами проверки компонентов

        Returns:
            str: Общий статус системы
        """
        # Если есть ошибки, общий статус - ошибка
        for component in components.values():
            if component.get("status") == "error":
                return "error"

        # Если есть нездоровые компоненты, общий статус - нездоров
        for component in components.values():
            if component.get("status") == "unhealthy":
                return "unhealthy"

        # Если есть деградировавшие компоненты, общий статус - деградация
        for component in components.values():
            if component.get("status") == "degraded":
                return "degraded"

        # Если все компоненты здоровы, общий статус - здоров
        return "healthy"

    async def get_cached_health_status(self, max_age: int = 30) -> dict[str, Any]:
        """
        Получение кэшированного статуса здоровья.

        Args:
            max_age: Максимальный возраст кэша в секундах

        Returns:
            Dict[str, Any]: Результаты проверки здоровья
        """
        current_time = time.time()

        # Если кэш еще актуален, возвращаем его
        if (current_time - self.last_check_time) < max_age and self.last_check_result:
            return self.last_check_result

        # Иначе выполняем новую проверку
        return await self.perform_health_check()

    def get_uptime(self) -> float:
        """
        Получение времени работы системы.

        Returns:
            float: Время работы в секундах
        """
        if hasattr(self, "_start_time"):
            return time.time() - self._start_time
        return 0.0

    def start_uptime_tracking(self) -> None:
        """Начало отслеживания времени работы."""
        self._start_time = time.time()


# Глобальный экземпляр сервиса проверки здоровья
health_check_service = HealthCheckService()
