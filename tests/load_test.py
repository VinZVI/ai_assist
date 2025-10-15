"""
@file: tests/load_test.py
@description: Скрипт нагрузочного тестирования для проверки масштабируемости
@dependencies: asyncio, httpx, loguru
@created: 2025-10-15
"""

import asyncio
import time
from typing import Any, Dict, List, Union

import httpx
from loguru import logger


class LoadTester:
    """Класс для нагрузочного тестирования бота."""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        """
        Инициализация нагрузочного тестера.

        Args:
            base_url: Базовый URL для тестирования
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        self.results: List[Dict[str, Any]] = []

    async def test_health_endpoint(
        self, concurrent_requests: int = 100
    ) -> Dict[str, Any]:
        """
        Тестирование эндпоинта здоровья.

        Args:
            concurrent_requests: Количество параллельных запросов

        Returns:
            dict: Результаты тестирования
        """
        logger.info(
            f"Начало тестирования эндпоинта здоровья с {concurrent_requests} параллельными запросами"
        )

        start_time = time.time()

        # Создаем задачи для параллельных запросов
        tasks = [self._make_health_request(i) for i in range(concurrent_requests)]

        # Выполняем все запросы параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        total_time = end_time - start_time

        # Анализируем результаты
        successful_requests = 0
        failed_requests = 0
        total_response_time = 0.0
        response_times = []

        for result in results:
            if isinstance(result, Exception):
                failed_requests += 1
                logger.error(f"Ошибка запроса: {result}")
            else:
                successful_requests += 1
                response_time = result["response_time"]
                total_response_time += response_time
                response_times.append(response_time)

        # Вычисляем статистику
        avg_response_time = (
            total_response_time / successful_requests if successful_requests > 0 else 0
        )
        requests_per_second = successful_requests / total_time if total_time > 0 else 0

        # Вычисляем перцентили
        response_times.sort()
        p50 = response_times[int(len(response_times) * 0.5)] if response_times else 0
        p95 = response_times[int(len(response_times) * 0.95)] if response_times else 0
        p99 = response_times[int(len(response_times) * 0.99)] if response_times else 0

        test_result = {
            "test_name": "health_endpoint",
            "concurrent_requests": concurrent_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "total_time": total_time,
            "requests_per_second": requests_per_second,
            "avg_response_time": avg_response_time,
            "p50_response_time": p50,
            "p95_response_time": p95,
            "p99_response_time": p99,
            "timestamp": time.time(),
        }

        self.results.append(test_result)

        logger.info(
            f"Тест завершен: {successful_requests}/{concurrent_requests} успешных запросов, "
            f"{requests_per_second:.2f} RPS, среднее время: {avg_response_time:.3f}с"
        )

        return test_result

    async def _make_health_request(
        self, request_id: int
    ) -> Dict[str, Union[int, float, bool, str]]:
        """
        Выполнение одного запроса к эндпоинту здоровья.

        Args:
            request_id: ID запроса

        Returns:
            dict: Результат запроса
        """
        start_time = time.time()

        try:
            response = await self.client.get(f"{self.base_url}/health")
            response_time = time.time() - start_time

            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code == 200,
            }
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Ошибка запроса {request_id}: {e}")

            return {
                "request_id": request_id,
                "status_code": 0,
                "response_time": response_time,
                "success": False,
                "error": str(e),
            }

    async def test_metrics_endpoint(
        self, concurrent_requests: int = 50
    ) -> Dict[str, Any]:
        """
        Тестирование эндпоинта метрик.

        Args:
            concurrent_requests: Количество параллельных запросов

        Returns:
            dict: Результаты тестирования
        """
        logger.info(
            f"Начало тестирования эндпоинта метрик с {concurrent_requests} параллельными запросами"
        )

        start_time = time.time()

        # Создаем задачи для параллельных запросов
        tasks = [self._make_metrics_request(i) for i in range(concurrent_requests)]

        # Выполняем все запросы параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        total_time = end_time - start_time

        # Анализируем результаты
        successful_requests = 0
        failed_requests = 0
        total_response_time = 0.0
        response_times = []

        for result in results:
            if isinstance(result, Exception):
                failed_requests += 1
                logger.error(f"Ошибка запроса: {result}")
            else:
                successful_requests += 1
                response_time = result["response_time"]
                total_response_time += response_time
                response_times.append(response_time)

        # Вычисляем статистику
        avg_response_time = (
            total_response_time / successful_requests if successful_requests > 0 else 0
        )
        requests_per_second = successful_requests / total_time if total_time > 0 else 0

        # Вычисляем перцентили
        response_times.sort()
        p50 = response_times[int(len(response_times) * 0.5)] if response_times else 0
        p95 = response_times[int(len(response_times) * 0.95)] if response_times else 0
        p99 = response_times[int(len(response_times) * 0.99)] if response_times else 0

        test_result = {
            "test_name": "metrics_endpoint",
            "concurrent_requests": concurrent_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "total_time": total_time,
            "requests_per_second": requests_per_second,
            "avg_response_time": avg_response_time,
            "p50_response_time": p50,
            "p95_response_time": p95,
            "p99_response_time": p99,
            "timestamp": time.time(),
        }

        self.results.append(test_result)

        logger.info(
            f"Тест завершен: {successful_requests}/{concurrent_requests} успешных запросов, "
            f"{requests_per_second:.2f} RPS, среднее время: {avg_response_time:.3f}с"
        )

        return test_result

    async def _make_metrics_request(
        self, request_id: int
    ) -> Dict[str, Union[int, float, bool, str]]:
        """
        Выполнение одного запроса к эндпоинту метрик.

        Args:
            request_id: ID запроса

        Returns:
            dict: Результат запроса
        """
        start_time = time.time()

        try:
            response = await self.client.get(f"{self.base_url}/metrics")
            response_time = time.time() - start_time

            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code == 200,
            }
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Ошибка запроса {request_id}: {e}")

            return {
                "request_id": request_id,
                "status_code": 0,
                "response_time": response_time,
                "success": False,
                "error": str(e),
            }

    async def run_comprehensive_test(self) -> List[Dict[str, Any]]:
        """
        Запуск комплексного нагрузочного тестирования.

        Returns:
            List[dict]: Результаты всех тестов
        """
        logger.info("Начало комплексного нагрузочного тестирования")

        # Тестируем эндпоинт здоровья с разным количеством параллельных запросов
        health_test_results = []
        for concurrent_requests in [10, 50, 100, 200]:
            result = await self.test_health_endpoint(concurrent_requests)
            health_test_results.append(result)
            # Небольшая пауза между тестами
            await asyncio.sleep(1)

        # Тестируем эндпоинт метрик
        metrics_test_results = []
        for concurrent_requests in [10, 50, 100]:
            result = await self.test_metrics_endpoint(concurrent_requests)
            metrics_test_results.append(result)
            # Небольшая пауза между тестами
            await asyncio.sleep(1)

        all_results = health_test_results + metrics_test_results

        # Выводим сводку результатов
        logger.info("Сводка результатов нагрузочного тестирования:")
        for result in all_results:
            logger.info(
                f"{result['test_name']}: {result['successful_requests']}/{result['concurrent_requests']} "
                f"успешных запросов, {result['requests_per_second']:.2f} RPS"
            )

        return all_results

    async def close(self) -> None:
        """Закрытие клиента."""
        await self.client.aclose()


async def main() -> None:
    """Главная функция для запуска нагрузочного тестирования."""
    logger.info("Запуск нагрузочного тестирования")

    tester = LoadTester()

    try:
        results = await tester.run_comprehensive_test()

        # Сохраняем результаты в файл
        import json

        with open("load_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info("Результаты тестирования сохранены в load_test_results.json")

    except Exception as e:
        logger.error(f"Ошибка во время тестирования: {e}")
    finally:
        await tester.close()


if __name__ == "__main__":
    # Настройка логирования
    logger.remove()
    logger.add(
        "load_test.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
    )
    logger.add(
        lambda msg: print(msg),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
    )

    # Запуск тестирования
    asyncio.run(main())
