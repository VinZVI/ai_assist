"""
@file: services/monitoring.py
@description: Сервис мониторинга производительности и отправки уведомлений
@dependencies: asyncio, loguru, app.services.health_check
@created: 2025-10-15
"""

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional
from collections import defaultdict, deque

from loguru import logger

from app.services.health_check import health_check_service
from app.middleware.metrics import MetricsMiddleware
from app.middleware.message_counter import MessageCountingMiddleware
from app.middleware.anti_spam import AntiSpamMiddleware
from app.middleware.rate_limit import RateLimitMiddleware


class MonitoringService:
    """Сервис мониторинга производительности и отправки уведомлений."""

    def __init__(self) -> None:
        """Инициализация сервиса мониторинга."""
        self.is_running = False
        self.monitoring_tasks: List[asyncio.Task] = []
        self.alert_handlers: List[Callable] = []
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.health_status_history: List[Dict[str, Any]] = []
        self.performance_stats: Dict[str, Any] = {
            "request_count": 0,
            "error_count": 0,
            "avg_response_time": 0.0,
            "active_users": 0,
            "messages_processed": 0,
            "blocked_requests": 0,
        }
        self.start_time = time.time()

    async def start_monitoring(self, interval: int = 60) -> None:
        """
        Запуск мониторинга системы.

        Args:
            interval: Интервал проверки в секундах
        """
        if self.is_running:
            logger.warning("Мониторинг уже запущен")
            return

        self.is_running = True
        logger.info(f"Запуск мониторинга с интервалом {interval} секунд")

        # Создаем задачу для периодической проверки здоровья
        health_check_task = asyncio.create_task(self._periodic_health_check(interval))
        self.monitoring_tasks.append(health_check_task)

        # Создаем задачу для сбора метрик
        metrics_task = asyncio.create_task(
            self._periodic_metrics_collection(interval // 2)
        )
        self.monitoring_tasks.append(metrics_task)

        # Создаем задачу для сбора аналитики
        analytics_task = asyncio.create_task(
            self._periodic_analytics_collection(interval // 4)
        )
        self.monitoring_tasks.append(analytics_task)

    async def stop_monitoring(self) -> None:
        """Остановка мониторинга системы."""
        if not self.is_running:
            logger.warning("Мониторинг не запущен")
            return

        self.is_running = False
        logger.info("Остановка мониторинга")

        # Отменяем все задачи мониторинга
        for task in self.monitoring_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self.monitoring_tasks.clear()

    async def _periodic_health_check(self, interval: int) -> None:
        """
        Периодическая проверка здоровья системы.

        Args:
            interval: Интервал проверки в секундах
        """
        while self.is_running:
            try:
                # Выполняем проверку здоровья
                health_result = await health_check_service.perform_health_check()

                # Сохраняем результат в историю
                self.health_status_history.append(health_result)

                # Ограничиваем размер истории
                if len(self.health_status_history) > 100:
                    self.health_status_history = self.health_status_history[-50:]

                # Проверяем, нужно ли отправлять уведомление
                if health_result["status"] in ["unhealthy", "degraded", "error"]:
                    await self._send_alert(health_result)

                logger.debug(
                    f"Проверка здоровья завершена. Статус: {health_result['status']}"
                )

            except Exception as e:
                logger.error(f"Ошибка при периодической проверке здоровья: {e}")

            # Ждем до следующей проверки
            await asyncio.sleep(interval)

    async def _periodic_metrics_collection(self, interval: int) -> None:
        """
        Периодический сбор метрик системы.

        Args:
            interval: Интервал сбора метрик в секундах
        """
        while self.is_running:
            try:
                # Собираем метрики из middleware
                metrics_data = self._collect_middleware_metrics()

                # Сохраняем метрики в историю
                timestamp = time.time()
                self.metrics_history["middleware_metrics"].append(
                    {"timestamp": timestamp, "data": metrics_data}
                )

                logger.debug("Сбор метрик системы завершен")

            except Exception as e:
                logger.error(f"Ошибка при сборе метрик: {e}")

            # Ждем до следующего сбора метрик
            await asyncio.sleep(interval)

    async def _periodic_analytics_collection(self, interval: int) -> None:
        """
        Периодический сбор аналитики.

        Args:
            interval: Интервал сбора аналитики в секундах
        """
        while self.is_running:
            try:
                # Собираем аналитику
                analytics_data = self._collect_analytics()

                # Сохраняем аналитику в историю
                timestamp = time.time()
                self.metrics_history["analytics"].append(
                    {"timestamp": timestamp, "data": analytics_data}
                )

                logger.debug("Сбор аналитики завершен")

            except Exception as e:
                logger.error(f"Ошибка при сборе аналитики: {e}")

            # Ждем до следующего сбора аналитики
            await asyncio.sleep(interval)

    def _collect_middleware_metrics(self) -> Dict[str, Any]:
        """
        Сбор метрик из middleware.

        Returns:
            Dict[str, Any]: Метрики из middleware
        """
        try:
            return {
                "metrics": MetricsMiddleware.get_metrics_stats(),
                "message_count": MessageCountingMiddleware.get_message_count_stats(),
                "anti_spam": AntiSpamMiddleware.get_anti_spam_stats(),
                "rate_limit": RateLimitMiddleware.get_rate_limit_stats(),
            }
        except Exception as e:
            logger.error(f"Ошибка при сборе метрик middleware: {e}")
            return {}

    def _collect_analytics(self) -> Dict[str, Any]:
        """
        Сбор аналитики.

        Returns:
            Dict[str, Any]: Аналитика системы
        """
        try:
            # Получаем метрики из middleware
            middleware_metrics = self._collect_middleware_metrics()

            # Вычисляем производительность
            uptime = time.time() - self.start_time
            requests_per_second = self.performance_stats["request_count"] / (
                uptime if uptime > 0 else 1
            )

            return {
                "performance": {
                    "uptime_seconds": uptime,
                    "requests_per_second": requests_per_second,
                    "total_requests": self.performance_stats["request_count"],
                    "total_errors": self.performance_stats["error_count"],
                    "avg_response_time": self.performance_stats["avg_response_time"],
                },
                "user_activity": {
                    "active_users": self.performance_stats["active_users"],
                    "messages_processed": self.performance_stats["messages_processed"],
                    "blocked_requests": self.performance_stats["blocked_requests"],
                },
                "middleware": middleware_metrics,
            }
        except Exception as e:
            logger.error(f"Ошибка при сборе аналитики: {e}")
            return {}

    async def _send_alert(self, health_result: Dict[str, Any]) -> None:
        """
        Отправка уведомления о проблеме.

        Args:
            health_result: Результаты проверки здоровья
        """
        alert_message = (
            f"⚠️ Проблема с ботом!\n"
            f"Статус: {health_result['status']}\n"
            f"Время: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        # Добавляем детали по компонентам
        for component_name, component_status in health_result["components"].items():
            status = component_status.get("status", "unknown")
            message = component_status.get("message", "")
            alert_message += f"{component_name}: {status} - {message}\n"

        logger.warning(alert_message)

        # Вызываем обработчики уведомлений
        for handler in self.alert_handlers:
            try:
                await handler(health_result)
            except Exception as e:
                logger.error(f"Ошибка в обработчике уведомлений: {e}")

    def register_alert_handler(self, handler: Callable) -> None:
        """
        Регистрация обработчика уведомлений.

        Args:
            handler: Функция-обработчик уведомлений
        """
        self.alert_handlers.append(handler)
        logger.info("Зарегистрирован новый обработчик уведомлений")

    def unregister_alert_handler(self, handler: Callable) -> None:
        """
        Удаление обработчика уведомлений.

        Args:
            handler: Функция-обработчик уведомлений
        """
        if handler in self.alert_handlers:
            self.alert_handlers.remove(handler)
            logger.info("Удален обработчик уведомлений")

    def get_health_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получение истории проверок здоровья.

        Args:
            limit: Максимальное количество записей

        Returns:
            List[Dict[str, Any]]: История проверок здоровья
        """
        return self.health_status_history[-limit:]

    def get_metrics_history(
        self, metric_name: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Получение истории метрик.

        Args:
            metric_name: Название метрики
            limit: Максимальное количество записей

        Returns:
            List[Dict[str, Any]]: История метрик
        """
        if metric_name in self.metrics_history:
            # Получаем последние записи
            records = list(self.metrics_history[metric_name])
            return records[-limit:]
        return []

    async def get_current_status(self) -> Dict[str, Any]:
        """
        Получение текущего статуса системы.

        Returns:
            Dict[str, Any]: Текущий статус системы
        """
        return await health_check_service.get_cached_health_status()

    def update_performance_stats(self, stat_name: str, value: Any) -> None:
        """
        Обновление статистики производительности.

        Args:
            stat_name: Название статистики
            value: Значение для обновления
        """
        if stat_name in self.performance_stats:
            self.performance_stats[stat_name] = value

    def increment_performance_counter(
        self, counter_name: str, increment: int = 1
    ) -> None:
        """
        Увеличение счетчика производительности.

        Args:
            counter_name: Название счетчика
            increment: Значение для увеличения
        """
        if counter_name in self.performance_stats:
            self.performance_stats[counter_name] += increment

    def get_analytics_summary(self) -> Dict[str, Any]:
        """
        Получение сводки аналитики.

        Returns:
            Dict[str, Any]: Сводка аналитики
        """
        try:
            # Получаем последние записи аналитики
            analytics_history = self.get_metrics_history("analytics", 1)
            if analytics_history:
                latest_analytics = analytics_history[0]["data"]
                return latest_analytics

            # Если нет данных, возвращаем пустую структуру
            return self._collect_analytics()
        except Exception as e:
            logger.error(f"Ошибка при получении сводки аналитики: {e}")
            return {}


# Глобальный экземпляр сервиса мониторинга
monitoring_service = MonitoringService()
