"""
Централизованная система управления зависимостями.
"""

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

from loguru import logger

T = TypeVar("T")


class DependencyContainer:
    """Контейнер для управления зависимостями приложения."""

    def __init__(self):
        self._services: dict[str, Any] = {}
        self._factories: dict[str, Callable] = {}
        self._singletons: dict[str, Any] = {}
        self._initialized = False

    def register_singleton(self, name: str, instance: Any) -> None:
        """Регистрация singleton сервиса."""
        self._singletons[name] = instance
        logger.debug(f"Registered singleton: {name}")

    def register_factory(self, name: str, factory: Callable) -> None:
        """Регистрация factory для создания сервисов."""
        self._factories[name] = factory
        logger.debug(f"Registered factory: {name}")

    def get(self, name: str) -> Any:
        """Получение сервиса по имени."""
        # Сначала проверяем singleton
        if name in self._singletons:
            return self._singletons[name]

        # Затем проверяем зарегистрированные сервисы
        if name in self._services:
            return self._services[name]

        # Создаем через factory если есть
        if name in self._factories:
            service = self._factories[name]()
            self._services[name] = service
            return service

        raise ValueError(f"Service '{name}' not found in container")

    async def get_async(self, name: str) -> Any:
        """Асинхронное получение сервиса."""
        service = self.get(name)

        # Если сервис имеет метод инициализации - вызываем его
        if hasattr(service, "initialize") and not getattr(
            service, "_initialized", False
        ):
            if asyncio.iscoroutinefunction(service.initialize):
                await service.initialize()
            else:
                service.initialize()
            service._initialized = True

        return service

    def inject(self, *dependencies: str):
        """Декоратор для внедрения зависимостей."""

        def decorator(func: Callable) -> Callable:
            if asyncio.iscoroutinefunction(func):

                async def async_wrapper(*args, **kwargs):
                    # Внедряем зависимости как keyword arguments
                    for dep_name in dependencies:
                        if dep_name not in kwargs:
                            kwargs[dep_name] = await self.get_async(dep_name)
                    return await func(*args, **kwargs)

                return async_wrapper

            def sync_wrapper(*args, **kwargs):
                for dep_name in dependencies:
                    if dep_name not in kwargs:
                        kwargs[dep_name] = self.get(dep_name)
                return func(*args, **kwargs)

            return sync_wrapper

        return decorator


# Глобальный контейнер
container = DependencyContainer()
