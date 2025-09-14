# AI-Компаньон: Telegram-бот для эмоциональной поддержки

## 1. Общие сведения о проекте

### 1.1 Назначение системы

Telegram-бот для предоставления эмоциональной поддержки и психологического комфорта пользователям с интеграцией DeepSeek API для генерации ответов на базе искусственного интеллекта.

### 1.2 Цели проекта

- Создание масштабируемого сервиса для психологической поддержки
- Обеспечение высокой доступности (99.9% uptime)
- Монетизация через премиум функции
- Создание MVP в течение 4-6 недель

## 2. Технический стек и архитектура

### 2.1 Основной стек технологий

```
Backend Framework: aiogram 3.x (асинхронный фреймворк для Telegram Bot API)
Language: Python 3.11+
Database: PostgreSQL 15+ (основная БД)
ORM: SQLAlchemy 2.0+ с async поддержкой
Migration Tool: Alembic
HTTP Client: httpx (для DeepSeek API)
Environment: python-dotenv
Validation: Pydantic
Logging: Loguru
Dependency Management: uv
```

### 2.2 Архитектурные компоненты

**Слой представления:**
- Telegram Bot API Handler (aiogram dispatcher)
- Webhook/Polling механизм обработки обновлений
- Middleware для аутентификации и rate limiting

**Бизнес-логика:**
- Conversation Manager (управление диалогами)
- AI Response Generator (интеграция с DeepSeek)
- User State Management (управление состояниями пользователей)
- Payment Processing (обработка платежей)

**Слой данных:**
- Database Abstraction Layer (SQLAlchemy ORM)
- Repository Pattern для работы с данными

### 2.3 Структура проекта

```
ai_assist/
├── app/                        # Основной пакет приложения
│   ├── __init__.py            # Инициализация пакета
│   ├── main.py                # Точка входа
│   ├── config.py              # Настройки приложения
│   ├── database.py            # Подключение к БД
│   ├── models/                # Модели данных
│   │   ├── __init__.py
│   │   ├── user.py           # Модель пользователя
│   │   └── conversation.py   # Модель диалога
│   ├── handlers/              # Обработчики команд
│   │   ├── __init__.py
│   │   ├── start.py          # /start команда
│   │   ├── conversation.py   # Обработка сообщений
│   │   ├── payment.py        # Обработка платежей
│   │   └── admin.py          # Админские команды
│   ├── services/              # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── ai_service.py     # DeepSeek интеграция
│   │   └── user_service.py   # Логика пользователей
│   ├── utils/                 # Утилиты
│   │   ├── __init__.py
│   │   ├── validators.py     # Валидация данных
│   │   ├── helpers.py        # Вспомогательные функции
│   │   └── logging.py        # Система логирования
│   └── keyboards/             # Клавиатуры
│       ├── __init__.py
│       └── basic.py          # Базовые клавиатуры
├── tests/                      # Тесты приложения
│   ├── __init__.py            # Инициализация пакета тестов
│   ├── conftest.py           # Конфигурация pytest
│   ├── test_config.py        # Тесты конфигурации
│   └── test_*.py             # Дополнительные тесты
├── docs/                      # Документация
│   ├── Project.md            # Описание проекта (этот файл)
│   ├── Tasktracker.md        # Отслеживание задач
│   ├── Diary.md              # Дневник разработки
│   ├── qa.md                 # Вопросы и ответы
│   └── changelog.md          # Журнал изменений
├── pyproject.toml            # Конфигурация проекта и зависимости
├── pytest.ini               # Конфигурация тестирования
├── .env.example              # Пример переменных окружения
├── docker-compose.yml        # Docker конфигурация
└── README.md                 # Основное описание проекта
```

## 3. AI сервис и интеграция

### 3.1 Архитектура AI сервиса

**Основные компоненты:**
- `AIService` - основной класс для работы с DeepSeek API
- `ResponseCache` - система кеширования ответов
- `ConversationMessage` - структура для сообщений диалога
- `AIResponse` - структура ответа от AI

**Особенности реализации:**
- Асинхронная работа с httpx клиентом
- Retry логика с экспоненциальной задержкой
- Обработка различных типов ошибок (401, 429, 5xx)
- Кеширование ответов на основе MD5 хешей
- Мониторинг состояния через `health_check()`

### 3.2 Конфигурация AI сервиса

```python
# Настройки DeepSeek API
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_MAX_TOKENS=1000
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_TIMEOUT=30

# Настройки кеширования
CACHE_TTL=3600
```

### 3.3 Обработка ошибок

**Иерархия ошибок:**
- `AIServiceError` - базовый класс ошибок
- `APIConnectionError` - ошибки подключения
- `APIRateLimitError` - превышение лимитов
- `APIAuthenticationError` - ошибки аутентификации

**Fallback стратегия:**
При ошибках API система возвращает предзаданные эмпатичные ответы.

## 4. Базы данных

### 3.1 Схема базы данных

**Таблица users:**
```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    is_premium BOOLEAN DEFAULT FALSE,
    daily_message_count INTEGER DEFAULT 0,
    last_message_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Таблица conversations:**
```sql
CREATE TABLE conversations (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    message_text TEXT NOT NULL,
    response_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 4. Этапы разработки

### 4.1 Этап 1: Подготовка инфраструктуры (3-5 дней)
- ✅ Настройка окружения с uv
- ✅ Создание структуры проекта
- 🔄 Настройка переменных окружения
- 🔄 Подключение к БД
- 🔄 Создание базовых моделей

### 4.2 Этап 2: Базовый функционал (7-10 дней)
- Обработчики команд (/start, текстовые сообщения)
- Интеграция с DeepSeek API
- Система лимитов сообщений
- Базовые клавиатуры

### 4.3 Этап 3: Монетизация (5-7 дней)
- Интеграция платежей (Telegram Stars)
- Премиум функции
- Статистика использования

### 4.4 Этап 4: Административные функции (3-5 дней)
- Админ-панель
- Статистика и аналитика
- Мониторинг

### 4.5 Этап 5: Тестирование и запуск (5-7 дней)
- Тестирование функций
- Деплой на VPS
- Мониторинг после запуска

## 5. Стандарты разработки

### 5.1 Кодирование
- Язык: Python 3.11+
- Стиль кода: PEP8
- Форматтер: ruff
- Сортировка импортов: isort
- Типизация: mypy (обязательная)
- Асинхронное программирование: async/await

### 5.2 Архитектурные принципы
- Запрет глобальных переменных
- Централизованное логирование (JSON формат)
- Обязательная обработка ошибок
- Repository Pattern для работы с данными
- Dependency Injection

### 5.3 Тестирование
- Минимальное покрытие: 80%
- Обязательные unit-тесты
- Интеграционные тесты
- Автоматические проверки в CI/CD

### 5.4 Структура тестов

Тесты организованы в отдельной папке `tests/` с следующей структурой:

```
tests/
├── __init__.py           # Инициализация пакета тестов
├── conftest.py          # Конфигурация pytest и фикстуры
├── test_config.py       # Тесты системы конфигурации
└── test_*.py           # Дополнительные тесты по компонентам
```

**Команды для запуска тестов:**

```bash
# Запуск всех тестов
uv run pytest

# Запуск тестов с покрытием
uv run pytest --cov=app

# Запуск конкретного файла тестов
uv run pytest tests/test_config.py

# Запуск тестов по маркерам
uv run pytest -m "config"  # Только тесты конфигурации
uv run pytest -m "not slow"  # Исключить медленные тесты
```

**Маркеры тестов:**
- `@pytest.mark.unit` - Юнит-тесты отдельных компонентов
- `@pytest.mark.integration` - Интеграционные тесты
- `@pytest.mark.config` - Тесты конфигурации
- `@pytest.mark.database` - Тесты базы данных
- `@pytest.mark.telegram` - Тесты Telegram интеграции
- `@pytest.mark.slow` - Медленные тесты

## 6. Переменные окружения

Основные переменные окружения, необходимые для работы приложения:

```env
# Telegram Bot
BOT_TOKEN=your_bot_token_here
WEBHOOK_URL=https://your-domain.com/webhook

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_assist
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=ai_assist
DATABASE_USER=postgres
DATABASE_PASSWORD=password

# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Admin
ADMIN_USER_ID=123456789

# Application
DEBUG=False
LOG_LEVEL=INFO
SECRET_KEY=your_secret_key_here
```

## 7. Безопасность и мониторинг

### 7.1 Безопасность
- Валидация всех входных данных
- Rate limiting для предотвращения спама
- Безопасное хранение токенов и ключей API
- Логирование критических операций

### 7.2 Мониторинг
- Логирование в JSON формате
- Отслеживание метрик производительности
- Алерты при критических ошибках
- Мониторинг использования API

## 8. Масштабирование

### 8.1 Горизонтальное масштабирование
- Stateless архитектура
- Возможность запуска нескольких инстансов
- Балансировка нагрузки

### 8.2 Оптимизация производительности
- Кеширование часто используемых данных
- Оптимизация запросов к БД
- Пулы соединений

Этот документ будет обновляться по мере развития проекта и добавления новых функций.