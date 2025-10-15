"""
@file: config/load_balancer.py
@description: Конфигурация балансировщика нагрузки для высокой доступности
@dependencies: pydantic
@created: 2025-10-15
"""

from typing import List

from pydantic import BaseModel, Field


class LoadBalancerConfig(BaseModel):
    """Конфигурация балансировщика нагрузки."""

    # Список серверов для балансировки
    servers: List[str] = Field(
        default=["http://localhost:8000"],
        description="Список серверов для балансировки нагрузки",
    )

    # Алгоритм балансировки
    algorithm: str = Field(
        default="round_robin",
        description="Алгоритм балансировки нагрузки (round_robin, least_connections, ip_hash)",
    )

    # Таймауты
    connection_timeout: int = Field(
        default=30, description="Таймаут подключения в секундах"
    )

    read_timeout: int = Field(default=30, description="Таймаут чтения в секундах")

    # Параметры проверки здоровья
    health_check_interval: int = Field(
        default=30, description="Интервал проверки здоровья в секундах"
    )

    health_check_path: str = Field(
        default="/health", description="Путь для проверки здоровья"
    )

    # Параметры повторных попыток
    retry_attempts: int = Field(
        default=3, description="Количество попыток повтора при ошибке"
    )

    retry_delay: int = Field(
        default=1, description="Задержка между попытками в секундах"
    )

    # Параметры отказоустойчивости
    failover_enabled: bool = Field(
        default=True, description="Включена ли отказоустойчивость"
    )

    # Параметры кэширования
    cache_enabled: bool = Field(default=True, description="Включено ли кэширование")

    cache_ttl: int = Field(default=300, description="Время жизни кэша в секундах")


# Экземпляр конфигурации балансировщика
load_balancer_config = LoadBalancerConfig()
