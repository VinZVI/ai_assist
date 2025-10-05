"""
@file: log_lexicon.py
@description: Сообщения для логирования в приложении (УСТАРЕЛ - ИСПОЛЬЗУЙТЕ МОДУЛЬНЫЕ ФАЙЛЫ)
@created: 2025-09-27
"""

# ПРЕДУПРЕЖДЕНИЕ: Этот файл устарел!
# Используйте модульные файлы лог-лексиконов из app/log_lexicon/:
# - app/log_lexicon/start.py для команды /start
# - app/log_lexicon/message.py для обработки сообщений
# - app/log_lexicon/callbacks.py для callback-запросов
# и т.д.

import warnings

warnings.warn(
    "app/log_lexicon.py устарел. Используйте модульные файлы из app/log_lexicon/.",
    DeprecationWarning,
    stacklevel=2,
)

# Сообщения логов для конфигурации
CONFIG_LOADED_SUCCESS = "✅ Конфигурация приложения загружена успешно"

# Сообщения логов для базы данных
DB_CONNECTING = "🔗 Создание подключения к базе данных..."
DB_ENGINE_CREATED = "✅ Движок базы данных создан: {db_url}"
DB_CHECK_EXISTENCE = "🔍 Проверка существования базы данных '{database_name}'..."
DB_EXISTS = "✅ База данных '{database_name}' уже существует"
DB_CREATING = "🏗️ Создание базы данных '{database_name}'..."
DB_CREATED = "✅ База данных '{database_name}' создана успешно"
DB_CREATE_ERROR = "❌ Ошибка при создании базы данных: {error}"
DB_CONTINUE_WITH_EXISTING = "⚠️ Продолжаем с существующей конфигурацией БД"
DB_CHECK_TABLES = "🔍 Проверка существования таблиц..."
DB_TABLES_EXIST = "✅ Таблицы уже существуют"
DB_CREATING_TABLES = "🏗️ Создание таблиц в базе данных..."
DB_TABLES_CREATED = "✅ Таблицы созданы успешно"
DB_TABLES_CHECK_ERROR = "⚠️ Не удалось проверить таблицы, создаем заново: {error}"
DB_INITIALIZED = "🎉 База данных инициализирована успешно"
DB_INIT_ERROR = "❌ Ошибка инициализации базы данных: {error}"
DB_CLOSING = "🔌 Закрытие подключения к базе данных..."
DB_CLOSED = "✅ Подключение к базе данных закрыто"
DB_CONNECTION_OK = "✅ Подключение к базе данных работает"
DB_CONNECTION_ERROR = "❌ Ошибка подключения к базе данных: {error}"
DB_NEW_SESSION = "📖 Создана новая сессия базы данных"
DB_SESSION_ENDED = "✅ Сессия базы данных закончена успешно"
DB_SQLALCHEMY_ERROR = "❌ Ошибка SQLAlchemy: {error}"
DB_UNEXPECTED_ERROR = "❌ Неожиданная ошибка в сессии БД: {error}"
DB_SESSION_CLOSED = "🔒 Сессия базы данных закрыта"

# Сообщения логов для бота
BOT_STARTING = "🚀 Запуск AI-Компаньон бота..."
BOT_DB_INITIALIZING = "📊 Инициализация базы данных..."
BOT_REGISTERED_ROUTERS = "✅ Зарегистрировано {count} роутеров"
BOT_STARTED = "🤖 Бот запущен: @{username} ({full_name})"
BOT_COMMANDS_SET = "✅ Команды бота настроены"
BOT_INITIALIZED = "✨ Бот успешно инициализирован и готов к работе!"
BOT_POLLING_STARTED = "📡 Запуск в режиме polling..."
BOT_WEBHOOK_STARTED = "🌐 Запуск в режиме webhook: {url}"
BOT_WEBHOOK_SET = "✅ Webhook настроен"
BOT_SHUTDOWN_STARTED = "🛑 Начинаю корректное завершение работы..."
BOT_POLLING_STOPPED = "📡 Polling остановлен"
BOT_POLLING_STOP_TIMEOUT = "⚠️ Таймаут при остановке polling"
BOT_SESSION_CLOSED = "🤖 Сессия бота закрыта"
BOT_SESSION_CLOSE_TIMEOUT = "⚠️ Таймаут при закрытии сессии бота"
BOT_DB_CLOSED = "🗄️ База данных закрыта"
BOT_DB_CLOSE_TIMEOUT = "⚠️ Таймаут при закрытии БД"
BOT_AI_MANAGER_CLOSED = "🤖 AI менеджер закрыт"
BOT_AI_MANAGER_CLOSE_TIMEOUT = "⚠️ Таймаут при закрытии AI менеджера"
BOT_SHUTDOWN_COMPLETED = "✅ Бот корректно завершил работу"
BOT_SHUTDOWN_ERROR = "❌ Ошибка при завершении работы: {error}"
BOT_SIGNAL_RECEIVED = "📡 Получен сигнал {signal}, инициирую завершение работы..."
BOT_KEYBOARD_INTERRUPT = "⌨️ Получено прерывание с клавиатуры"
BOT_CRITICAL_ERROR = "💥 Критическая ошибка: {error}"
BOT_USER_INTERRUPTED = "👋 Работа бота прервана пользователем"
BOT_PROGRAM_FINISHED = "🏁 Программа завершена"

# Сообщения логов для AI менеджера
AI_MANAGER_INITIALIZING = "🔧 Инициализация AI провайдеров..."
AI_MANAGER_DEEPSEEK_INITIALIZED = "✅ DeepSeek провайдер инициализирован"
AI_MANAGER_OPENROUTER_INITIALIZED = "✅ OpenRouter провайдер инициализирован"
AI_MANAGER_ACTIVE_PROVIDERS = "🎯 Активные провайдеры: {providers}"
AI_MANAGER_INITIALIZED = "🤖 AI менеджер инициализирован"
AI_MANAGER_PROVIDER_ATTEMPT = "🎯 Попытка {attempt}: использование {provider}"
AI_MANAGER_REQUEST = "🚀 Запрос к {provider}..."
AI_MANAGER_RESPONSE_RECEIVED = "✅ Успешный ответ от {provider} API за {duration}s"
AI_MANAGER_ERROR = "❌ Ошибка при запросе к {provider}: {error}"
AI_MANAGER_FALLBACK = "🔄 Использование резервного провайдера {fallback_provider}"
AI_MANAGER_ALL_PROVIDERS_FAILED = "💥 Все провайдеры недоступны"
AI_MANAGER_HEALTH_CHECK = "🏥 Проверка состояния провайдеров..."
AI_MANAGER_HEALTH_CHECK_RESULT = "📊 Результаты проверки: {results}"
AI_MANAGER_CACHE_CLEARED = "🧹 Кеш AI менеджера очищен"
AI_MANAGER_SHUTTING_DOWN = "🛑 Завершение работы AI менеджера..."
AI_MANAGER_SHUTDOWN_COMPLETED = "✅ AI менеджер завершил работу"
AI_MANAGER_SHUTDOWN_ERROR = "❌ Ошибка при завершении работы AI менеджера: {error}"

# Сообщения логов для AI провайдеров
AI_PROVIDER_INITIALIZING = "🔧 Инициализация {provider} провайдера..."
AI_PROVIDER_HTTP_CLIENT_CREATED = "🔗 HTTP клиент для {provider} API создан"
AI_PROVIDER_CONFIGURED = "✅ {provider} провайдер настроен"
AI_PROVIDER_NOT_CONFIGURED = "⚠️ {provider} провайдер не настроен"
AI_PROVIDER_AVAILABLE = "✅ {provider} API доступен"
AI_PROVIDER_UNAVAILABLE = "❌ {provider} API недоступен: {error}"
AI_PROVIDER_RESPONSE = (
    "🤖 {provider} ответ: {chars} символов, {tokens} токенов, {duration}s"
)
AI_PROVIDER_REQUEST_ERROR = "❌ Ошибка запроса к {provider}: {error}"
AI_PROVIDER_TIMEOUT = "⏰ Таймаут запроса к {provider} ({timeout}s)"
AI_PROVIDER_RATE_LIMIT = "🚦 Превышен лимит запросов к {provider}, ожидание {delay}s"
AI_PROVIDER_INVALID_RESPONSE = "⚠️ Невалидный ответ от {provider}: {error}"

# Сообщения логов для обработчиков сообщений
MESSAGE_RECEIVED = "💬 Получено сообщение от пользователя {user_id}: {chars} символов"
MESSAGE_USER_LIMIT_EXCEEDED = "⚠️ Пользователь {user_id} превысил лимит сообщений"
MESSAGE_PROCESSING = "⚙️ Обработка сообщения пользователя {user_id}"
MESSAGE_AI_RESPONSE = (
    "🤖 AI ответ получен от {provider}: {chars} символов, {tokens} токенов, {duration}s"
)
MESSAGE_SENT = (
    "✅ Ответ отправлен пользователю {user_id}: {chars} символов, "
    "{tokens} токенов, {duration}s"
)
MESSAGE_ERROR = "❌ Ошибка при обработке сообщения от пользователя {user_id}: {error}"

# Сообщения логов для пользователей
USER_CREATED = "👤 Создан новый пользователь {user_id} (@{username})"
USER_UPDATED = "📝 Обновлена информация пользователя {user_id}"
USER_BLOCKED = "🚫 Пользователь {user_id} заблокирован"
USER_UNBLOCKED = "✅ Пользователь {user_id} разблокирован"
USER_PREMIUM_ACTIVATED = "💎 Активирован премиум для пользователя {user_id}"
USER_PREMIUM_EXPIRED = "⏰ Премиум пользователя {user_id} истек"
USER_MESSAGE_COUNT_RESET = "🔄 Сброшен счетчик сообщений пользователя {user_id}"
USER_ACTIVITY_RECORDED = "📈 Записана активность пользователя {user_id}"
USER_PROFILE_REQUESTED = "👤 Запрошена информация о пользователе {user_id}"
USER_STATS_REQUESTED = "📊 Запрошена статистика пользователя {user_id}"
USER_PAYMENT_INITIATED = "💳 Инициирован платеж пользователя {user_id}"
USER_PAYMENT_COMPLETED = "💰 Платеж пользователя {user_id} успешно обработан"
USER_PAYMENT_FAILED = "❌ Ошибка платежа пользователя {user_id}: {error}"

# Сообщения логов для администрирования
ADMIN_COMMAND_RECEIVED = "🛡️ Получена админ-команда {command} от пользователя {user_id}"
ADMIN_USER_LIST_REQUESTED = "📋 Запрошен список пользователей админом {user_id}"
ADMIN_USER_BLOCKED = "🔐 Админ {admin_id} заблокировал пользователя {user_id}"
ADMIN_USER_UNBLOCKED = "🔓 Админ {admin_id} разблокировал пользователя {user_id}"
ADMIN_STATS_REQUESTED = "📈 Админ {user_id} запросил статистику системы"
ADMIN_DB_BACKUP_STARTED = "💾 Начато резервное копирование БД админом {user_id}"
ADMIN_DB_BACKUP_COMPLETED = "✅ Резервное копирование БД завершено"
ADMIN_DB_BACKUP_ERROR = "❌ Ошибка резервного копирования БД: {error}"
ADMIN_CONFIG_RELOADED = "🔄 Админ {user_id} перезагрузил конфигурацию"
ADMIN_BROADCAST_SENT = (
    "📢 Админ {user_id} отправил широковещательное сообщение ({count} пользователей)"
)
ADMIN_BROADCAST_ERROR = "❌ Ошибка широковещательной рассылки: {error}"

# Сообщения логов для платежей
PAYMENT_PROVIDER_INITIALIZED = "💳 Инициализирован платежный провайдер {provider}"
PAYMENT_PROVIDER_ERROR = "❌ Ошибка платежного провайдера {provider}: {error}"
PAYMENT_WEBHOOK_RECEIVED = "💳 Получен webhook платежа от {provider}"
PAYMENT_WEBHOOK_PROCESSED = "✅ Webhook платежа обработан"
PAYMENT_WEBHOOK_ERROR = "❌ Ошибка обработки webhook платежа: {error}"
PAYMENT_CREATED = "💸 Создан платеж для пользователя {user_id}: {amount} {currency}"
PAYMENT_COMPLETED = "💰 Платеж {payment_id} пользователя {user_id} успешно завершен"
PAYMENT_CANCELLED = "↩️ Платеж {payment_id} пользователя {user_id} отменен"
PAYMENT_REFUNDED = "🔙 Платеж {payment_id} пользователя {user_id} возвращен"
PAYMENT_FAILED = "❌ Платеж {payment_id} пользователя {user_id} не удался: {error}"

# Сообщения логов для мониторинга
MONITORING_METRIC = "📊 Метрика: {metric} = {value}"
MONITORING_HEALTH_CHECK = "🏥 Проверка состояния системы..."
MONITORING_HEALTH_OK = "✅ Система работает нормально"
MONITORING_HEALTH_ERROR = "❌ Проблемы со здоровьем системы: {error}"
MONITORING_PERFORMANCE = "⏱️ {operation} выполнено за {duration}ms"
MONITORING_RESOURCE_USAGE = "🖥️ Использование ресурсов: CPU {cpu}%, RAM {ram}%"
MONITORING_ALERT = "🚨 Алерт: {alert}"
MONITORING_ALERT_RESOLVED = "✅ Алерт разрешен: {alert}"
