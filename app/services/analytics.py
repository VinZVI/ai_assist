"""
@file: services/analytics.py
@description: Сервис аналитики для получения детальных сведений о производительности бота
@dependencies: asyncio, loguru, app.services.monitoring
@created: 2025-10-15
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta

from loguru import logger

from app.services.monitoring import monitoring_service


class AnalyticsService:
    """Сервис аналитики для получения детальных сведений о производительности бота."""

    def __init__(self) -> None:
        """Инициализация сервиса аналитики."""
        self.analytics_data: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.is_collecting = False
        self.collection_task: Optional[asyncio.Task] = None

    async def start_analytics_collection(self, interval: int = 300) -> None:
        """
        Запуск сбора аналитики.

        Args:
            interval: Интервал сбора аналитики в секундах
        """
        if self.is_collecting:
            logger.warning("Сбор аналитики уже запущен")
            return

        self.is_collecting = True
        logger.info(f"Запуск сбора аналитики с интервалом {interval} секунд")

        self.collection_task = asyncio.create_task(
            self._periodic_analytics_collection(interval)
        )

    async def stop_analytics_collection(self) -> None:
        """Остановка сбора аналитики."""
        if not self.is_collecting:
            logger.warning("Сбор аналитики не запущен")
            return

        self.is_collecting = False
        logger.info("Остановка сбора аналитики")

        if self.collection_task and not self.collection_task.done():
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass

    async def _periodic_analytics_collection(self, interval: int) -> None:
        """
        Периодический сбор аналитики.

        Args:
            interval: Интервал сбора аналитики в секундах
        """
        while self.is_collecting:
            try:
                # Собираем аналитику
                analytics_data = await self.collect_analytics()

                # Сохраняем данные
                timestamp = time.time()
                self.analytics_data["general"].append(
                    {"timestamp": timestamp, "data": analytics_data}
                )

                # Ограничиваем размер истории
                if len(self.analytics_data["general"]) > 1000:
                    self.analytics_data["general"] = self.analytics_data["general"][
                        -500:
                    ]

                logger.debug("Сбор аналитики завершен")

            except Exception as e:
                logger.error(f"Ошибка при сборе аналитики: {e}")

            # Ждем до следующего сбора
            await asyncio.sleep(interval)

    async def collect_analytics(self) -> Dict[str, Any]:
        """
        Сбор аналитики по всем аспектам работы бота.

        Returns:
            Dict[str, Any]: Собранные данные аналитики
        """
        try:
            # Получаем сводку аналитики из сервиса мониторинга
            analytics_summary = monitoring_service.get_analytics_summary()

            # Собираем дополнительные данные
            additional_data = {
                "timestamp": time.time(),
                "collected_at": datetime.now().isoformat(),
                "uptime": self._calculate_uptime(),
                "user_engagement": await self._analyze_user_engagement(),
                "message_patterns": await self._analyze_message_patterns(),
                "performance_trends": await self._analyze_performance_trends(),
                "error_analysis": await self._analyze_errors(),
            }

            # Объединяем данные
            combined_data = {**analytics_summary, **additional_data}

            return combined_data

        except Exception as e:
            logger.error(f"Ошибка при сборе аналитики: {e}")
            return {"error": str(e), "timestamp": time.time()}

    def _calculate_uptime(self) -> Dict[str, Any]:
        """
        Вычисление времени работы системы.

        Returns:
            Dict[str, Any]: Информация о времени работы
        """
        try:
            # Получаем аналитику из сервиса мониторинга
            analytics_summary = monitoring_service.get_analytics_summary()
            performance = analytics_summary.get("performance", {})

            uptime_seconds = performance.get("uptime_seconds", 0)

            # Конвертируем в удобочитаемый формат
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            seconds = int(uptime_seconds % 60)

            return {
                "total_seconds": uptime_seconds,
                "formatted": f"{days}d {hours}h {minutes}m {seconds}s",
                "days": days,
                "hours": hours,
                "minutes": minutes,
                "seconds": seconds,
            }
        except Exception as e:
            logger.error(f"Ошибка при вычислении времени работы: {e}")
            return {"total_seconds": 0, "formatted": "0d 0h 0m 0s", "error": str(e)}

    async def _analyze_user_engagement(self) -> Dict[str, Any]:
        """
        Анализ вовлеченности пользователей.

        Returns:
            Dict[str, Any]: Анализ вовлеченности
        """
        try:
            # Получаем аналитику из сервиса мониторинга
            analytics_summary = monitoring_service.get_analytics_summary()
            user_activity = analytics_summary.get("user_activity", {})
            message_count = analytics_summary.get("middleware", {}).get(
                "message_count", {}
            )

            total_messages = message_count.get("total_messages", 0)
            free_messages = message_count.get("free_user_messages", 0)
            premium_messages = message_count.get("premium_user_messages", 0)

            active_users = user_activity.get("active_users", 0)
            messages_processed = user_activity.get("messages_processed", 0)

            # Вычисляем метрики вовлеченности
            engagement_metrics = {
                "total_messages": total_messages,
                "free_user_messages": free_messages,
                "premium_user_messages": premium_messages,
                "active_users": active_users,
                "messages_per_user": messages_processed / active_users
                if active_users > 0
                else 0,
                "premium_user_ratio": premium_messages / total_messages
                if total_messages > 0
                else 0,
                "message_volume_trend": await self._analyze_message_volume_trend(),
            }

            return engagement_metrics
        except Exception as e:
            logger.error(f"Ошибка при анализе вовлеченности: {e}")
            return {"error": str(e)}

    async def _analyze_message_volume_trend(self) -> Dict[str, Any]:
        """
        Анализ тренда объема сообщений.

        Returns:
            Dict[str, Any]: Анализ тренда объема сообщений
        """
        try:
            # Получаем историю метрик сообщений
            message_history = monitoring_service.get_metrics_history(
                "middleware_metrics", 24
            )

            if len(message_history) < 2:
                return {"trend": "insufficient_data", "change_percent": 0}

            # Сравниваем последние два периода
            latest = (
                message_history[-1]["data"]
                .get("message_count", {})
                .get("total_messages", 0)
            )
            previous = (
                message_history[-2]["data"]
                .get("message_count", {})
                .get("total_messages", 0)
            )

            if previous == 0:
                change_percent = 100 if latest > 0 else 0
            else:
                change_percent = ((latest - previous) / previous) * 100

            trend = (
                "increasing"
                if change_percent > 0
                else "decreasing"
                if change_percent < 0
                else "stable"
            )

            return {
                "trend": trend,
                "change_percent": round(change_percent, 2),
                "latest_count": latest,
                "previous_count": previous,
            }
        except Exception as e:
            logger.error(f"Ошибка при анализе тренда объема сообщений: {e}")
            return {"trend": "error", "change_percent": 0, "error": str(e)}

    async def _analyze_message_patterns(self) -> Dict[str, Any]:
        """
        Анализ паттернов сообщений.

        Returns:
            Dict[str, Any]: Анализ паттернов сообщений
        """
        try:
            # Получаем аналитику из сервиса мониторинга
            analytics_summary = monitoring_service.get_analytics_summary()
            message_count = analytics_summary.get("middleware", {}).get(
                "message_count", {}
            )
            anti_spam = analytics_summary.get("middleware", {}).get("anti_spam", {})
            rate_limit = analytics_summary.get("middleware", {}).get("rate_limit", {})

            # Анализируем паттерны
            patterns = {
                "spam_detection": {
                    "actions_blocked": anti_spam.get("actions_blocked", 0),
                    "users_blocked": anti_spam.get("users_blocked", 0),
                    "spam_rate": anti_spam.get("actions_blocked", 0)
                    / message_count.get("total_messages", 1)
                    if message_count.get("total_messages", 0) > 0
                    else 0,
                },
                "rate_limiting": {
                    "requests_limited": rate_limit.get("requests_limited", 0),
                    "users_limited": rate_limit.get("users_limited", 0),
                    "limit_rate": rate_limit.get("requests_limited", 0)
                    / message_count.get("total_messages", 1)
                    if message_count.get("total_messages", 0) > 0
                    else 0,
                },
                "user_distribution": {
                    "free_users": message_count.get("free_user_messages", 0),
                    "premium_users": message_count.get("premium_user_messages", 0),
                    "premium_ratio": message_count.get("premium_user_messages", 0)
                    / message_count.get("total_messages", 1)
                    if message_count.get("total_messages", 0) > 0
                    else 0,
                },
            }

            return patterns
        except Exception as e:
            logger.error(f"Ошибка при анализе паттернов сообщений: {e}")
            return {"error": str(e)}

    async def _analyze_performance_trends(self) -> Dict[str, Any]:
        """
        Анализ трендов производительности.

        Returns:
            Dict[str, Any]: Анализ трендов производительности
        """
        try:
            # Получаем аналитику из сервиса мониторинга
            analytics_summary = monitoring_service.get_analytics_summary()
            performance = analytics_summary.get("performance", {})

            # Анализируем тренды
            trends = {
                "requests_per_second": performance.get("requests_per_second", 0),
                "avg_response_time": performance.get("avg_response_time", 0),
                "error_rate": performance.get("total_errors", 0)
                / performance.get("total_requests", 1)
                if performance.get("total_requests", 0) > 0
                else 0,
                "uptime_percentage": (
                    performance.get("uptime_seconds", 0)
                    / (time.time() - monitoring_service.start_time)
                )
                * 100
                if time.time() > monitoring_service.start_time
                else 100,
            }

            return trends
        except Exception as e:
            logger.error(f"Ошибка при анализе трендов производительности: {e}")
            return {"error": str(e)}

    async def _analyze_errors(self) -> Dict[str, Any]:
        """
        Анализ ошибок.

        Returns:
            Dict[str, Any]: Анализ ошибок
        """
        try:
            # Получаем аналитику из сервиса мониторинга
            analytics_summary = monitoring_service.get_analytics_summary()
            performance = analytics_summary.get("performance", {})
            middleware_metrics = analytics_summary.get("middleware", {})

            # Анализируем ошибки
            error_analysis = {
                "total_errors": performance.get("total_errors", 0),
                "error_rate": performance.get("total_errors", 0)
                / performance.get("total_requests", 1)
                if performance.get("total_requests", 0) > 0
                else 0,
                "middleware_errors": {
                    "metrics_errors": middleware_metrics.get("metrics", {}).get(
                        "errors_occurred", 0
                    ),
                    "anti_spam_errors": middleware_metrics.get("anti_spam", {}).get(
                        "errors_occurred", 0
                    )
                    if "anti_spam" in middleware_metrics
                    else 0,
                    "rate_limit_errors": middleware_metrics.get("rate_limit", {}).get(
                        "errors_occurred", 0
                    )
                    if "rate_limit" in middleware_metrics
                    else 0,
                },
            }

            return error_analysis
        except Exception as e:
            logger.error(f"Ошибка при анализе ошибок: {e}")
            return {"error": str(e)}

    def get_analytics_report(self, period_hours: int = 24) -> Dict[str, Any]:
        """
        Получение отчета по аналитике за указанный период.

        Args:
            period_hours: Период в часах

        Returns:
            Dict[str, Any]: Отчет по аналитике
        """
        try:
            # Вычисляем время начала периода
            end_time = time.time()
            start_time = end_time - (period_hours * 3600)

            # Фильтруем данные за период
            period_data = []
            for data_list in self.analytics_data.values():
                for record in data_list:
                    if start_time <= record["timestamp"] <= end_time:
                        period_data.append(record)

            if not period_data:
                return {
                    "error": "Нет данных за указанный период",
                    "period_hours": period_hours,
                }

            # Генерируем отчет
            report = {
                "period_hours": period_hours,
                "report_generated": datetime.now().isoformat(),
                "total_data_points": len(period_data),
                "summary": self._generate_summary(period_data),
                "trends": self._generate_trends(period_data),
                "recommendations": self._generate_recommendations(period_data),
            }

            return report
        except Exception as e:
            logger.error(f"Ошибка при генерации отчета: {e}")
            return {"error": str(e), "period_hours": period_hours}

    def _generate_summary(self, period_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Генерация сводки по данным.

        Args:
            period_data: Данные за период

        Returns:
            Dict[str, Any]: Сводка
        """
        try:
            if not period_data:
                return {}

            # Берем последние данные для сводки
            latest_data = period_data[-1]["data"]

            return {
                "latest_metrics": latest_data.get("performance", {}),
                "user_activity": latest_data.get("user_activity", {}),
                "message_patterns": latest_data.get("message_patterns", {}),
            }
        except Exception as e:
            logger.error(f"Ошибка при генерации сводки: {e}")
            return {}

    def _generate_trends(self, period_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Генерация трендов по данным.

        Args:
            period_data: Данные за период

        Returns:
            Dict[str, Any]: Тренды
        """
        try:
            if len(period_data) < 2:
                return {"trend_analysis": "Недостаточно данных для анализа трендов"}

            # Анализируем изменения между первыми и последними данными
            first_data = period_data[0]["data"]
            last_data = period_data[-1]["data"]

            return {
                "period_start": datetime.fromtimestamp(
                    period_data[0]["timestamp"]
                ).isoformat(),
                "period_end": datetime.fromtimestamp(
                    period_data[-1]["timestamp"]
                ).isoformat(),
                "data_points": len(period_data),
            }
        except Exception as e:
            logger.error(f"Ошибка при генерации трендов: {e}")
            return {"error": str(e)}

    def _generate_recommendations(self, period_data: List[Dict[str, Any]]) -> List[str]:
        """
        Генерация рекомендаций по данным.

        Args:
            period_data: Данные за период

        Returns:
            List[str]: Рекомендации
        """
        try:
            recommendations = []

            if not period_data:
                return recommendations

            # Берем последние данные для анализа
            latest_data = period_data[-1]["data"]

            # Анализ производительности
            performance = latest_data.get("performance", {})
            if performance.get("requests_per_second", 0) > 100:
                recommendations.append(
                    "Высокая нагрузка: рассмотрите возможность масштабирования"
                )

            # Анализ ошибок
            error_analysis = latest_data.get("error_analysis", {})
            if error_analysis.get("error_rate", 0) > 0.05:  # Более 5% ошибок
                recommendations.append(
                    "Высокий уровень ошибок: проверьте логи и устраните проблемы"
                )

            # Анализ пользователей
            user_engagement = latest_data.get("user_engagement", {})
            if (
                user_engagement.get("premium_user_ratio", 0) < 0.1
            ):  # Менее 10% премиум пользователей
                recommendations.append(
                    "Низкий уровень премиум подписок: рассмотрите маркетинговые кампании"
                )

            return recommendations
        except Exception as e:
            logger.error(f"Ошибка при генерации рекомендаций: {e}")
            return ["Ошибка при генерации рекомендаций"]


# Глобальный экземпляр сервиса аналитики
analytics_service = AnalyticsService()
