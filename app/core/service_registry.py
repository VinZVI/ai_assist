"""Реестр сервисов приложения."""

from loguru import logger

from app.core.dependencies import container


async def initialize_services() -> None:
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


async def _initialize_database_services() -> None:
    """Инициализация сервисов БД."""
    from app.database import get_session, init_db

    # Инициализируем БД
    await init_db()

    # Регистрируем фабрику сессий
    container.register_factory("db_session", get_session)

    logger.info("Database services initialized")


async def _initialize_cache_services() -> None:
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


async def _initialize_business_services() -> None:
    """Инициализация бизнес-сервисов."""
    from app.services.ai_manager import get_ai_manager
    from app.services.conversation import ConversationService
    from app.services.user_service import UserService
    from app.services.subscription_service import SubscriptionService
    from app.config import get_config
    from app.database import get_session

    # Создаем экземпляры сервисов
    conversation_service = ConversationService()
    user_service = UserService()
    ai_manager = get_ai_manager()
    config = get_config()
    
    # Create a factory function for subscription service that gets db session each time
    async def create_subscription_service():
        # Create a new session for each service instance
        async with get_session() as session:
            return SubscriptionService(session, config)
    
    # For now, create a single instance with a session
    # In a real application, you'd want to create sessions per request
    subscription_service = SubscriptionService.__new__(SubscriptionService)
    subscription_service.config = config

    # Регистрируем сервисы
    container.register_singleton("config", config)
    container.register_singleton("conversation_service", conversation_service)
    container.register_singleton("user_service", user_service)
    container.register_singleton("ai_manager", ai_manager)
    container.register_singleton("subscription_service", subscription_service)
    
    # Also register a factory for creating subscription services with proper sessions
    container.register_factory("subscription_service_factory", create_subscription_service)

    logger.info("Business services initialized")


async def _initialize_monitoring_services() -> None:
    """Инициализация сервисов мониторинга."""
    # Пока оставим пустым, реализуем позже
