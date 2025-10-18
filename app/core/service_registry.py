"""
Реестр сервисов приложения.
"""

from app.core.dependencies import container
from loguru import logger


async def initialize_services():
    """Инициализация всех сервисов приложения."""

    # 1. Инициализируем базовые сервисы
    await _initialize_database_services()

    # 2. Инициализируем кэширование
    await _initialize_cache_services()

    # 3. Инициализируем бизнес-сервисы
    await _initialize_business_services()

    # 4. Инициализируем мониторинг (если реализован)
    await _initialize_monitoring_services()

    logger.info("All services initialized successfully")


async def _initialize_database_services():
    """Инициализация сервисов БД."""
    from app.database import init_db, get_session

    # Инициализируем БД
    await init_db()

    # Регистрируем фабрику сессий
    container.register_factory("db_session", get_session)

    logger.info("Database services initialized")


async def _initialize_cache_services():
    """Инициализация сервисов кэширования."""
    from app.services.cache_service import cache_service
    from app.services.redis_cache_service import initialize_redis_cache

    # Инициализируем Redis
    redis_cache = await initialize_redis_cache()
    if redis_cache:
        container.register_singleton("redis_cache", redis_cache)

    # Инициализируем основной сервис кэша
    await cache_service.initialize_redis_cache()
    container.register_singleton("cache_service", cache_service)

    logger.info("Cache services initialized")


async def _initialize_business_services():
    """Инициализация бизнес-сервисов."""
    from app.services.conversation_service import ConversationService
    from app.services.user_service import UserService
    from app.services.ai_manager import get_ai_manager

    # Создаем экземпляры сервисов
    conversation_service = ConversationService()
    user_service = UserService()
    ai_manager = get_ai_manager()

    # Регистрируем сервисы
    container.register_singleton("conversation_service", conversation_service)
    container.register_singleton("user_service", user_service)
    container.register_singleton("ai_manager", ai_manager)

    logger.info("Business services initialized")


async def _initialize_monitoring_services():
    """Инициализация сервисов мониторинга."""
    # Пока оставим пустым, реализуем позже
    pass
