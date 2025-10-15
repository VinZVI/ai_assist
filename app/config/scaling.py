"""
@file: config/scaling.py
@description: Конфигурация масштабирования для поддержки горизонтального масштабирования
@dependencies: pydantic
@created: 2025-10-15
"""

from typing import List

from pydantic import BaseModel, Field


class ScalingConfig(BaseModel):
    """Конфигурация масштабирования."""

    # Параметры горизонтального масштабирования
    enable_horizontal_scaling: bool = Field(
        default=True, description="Включено ли горизонтальное масштабирование"
    )

    # Количество экземпляров бота
    min_instances: int = Field(
        default=1, description="Минимальное количество экземпляров бота"
    )

    max_instances: int = Field(
        default=10, description="Максимальное количество экземпляров бота"
    )

    # Пороги для автоматического масштабирования
    scale_up_threshold: float = Field(
        default=0.8, description="Порог загрузки для масштабирования вверх (0.0 - 1.0)"
    )

    scale_down_threshold: float = Field(
        default=0.3, description="Порог загрузки для масштабирования вниз (0.0 - 1.0)"
    )

    # Интервал проверки для масштабирования
    scaling_check_interval: int = Field(
        default=60, description="Интервал проверки масштабирования в секундах"
    )

    # Параметры вертикального масштабирования
    enable_vertical_scaling: bool = Field(
        default=True, description="Включено ли вертикальное масштабирование"
    )

    # Параметры кэширования для масштабирования
    cache_enabled: bool = Field(default=True, description="Включено ли кэширование")

    cache_backend: str = Field(
        default="redis", description="Бэкенд кэширования (redis, memory)"
    )

    cache_hosts: list[str] = Field(
        default=["localhost:6379"], description="Список хостов кэширования"
    )

    cache_ttl: int = Field(default=300, description="Время жизни кэша в секундах")

    # Параметры очереди сообщений
    message_queue_enabled: bool = Field(
        default=True, description="Включена ли очередь сообщений"
    )

    message_queue_backend: str = Field(
        default="redis", description="Бэкенд очереди сообщений (redis, rabbitmq)"
    )

    message_queue_hosts: list[str] = Field(
        default=["localhost:6379"], description="Список хостов очереди сообщений"
    )

    # Параметры сессий для масштабирования
    session_backend: str = Field(
        default="redis", description="Бэкенд сессий (redis, database)"
    )

    session_hosts: list[str] = Field(
        default=["localhost:6379"], description="Список хостов сессий"
    )

    # Параметры распределенной блокировки
    distributed_lock_enabled: bool = Field(
        default=True, description="Включена ли распределенная блокировка"
    )

    lock_backend: str = Field(
        default="redis",
        description="Бэкенд распределенной блокировки (redis, zookeeper)",
    )

    lock_hosts: list[str] = Field(
        default=["localhost:6379"], description="Список хостов блокировок"
    )


# Экземпляр конфигурации масштабирования
scaling_config = ScalingConfig()
