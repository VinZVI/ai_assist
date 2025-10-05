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
Validation: Pydantic v2.11.7
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
│   │   ├── message.py        # Обработка сообщений
│   │   ├── callbacks.py      # Обработка callback-запросов
│   │   ├── payment.py        # Обработка платежей
│   │   └── admin.py          # Админские команды
│   ├── services/              # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── ai_manager.py     # Менеджер AI провайдеров
│   │   ├── ai_service.py     # Устаревший файл
│   │   ├── ai_providers/     # Провайдеры AI
│   │   │   ├── __init__.py
│   │   │   ├── base.py       # Базовый класс провайдера
│   │   │   ├── deepseek.py   # DeepSeek провайдер
│   │   │   └── openrouter.py # OpenRouter провайдер
│   │   └── user_service.py   # Логика пользователей
│   ├── utils/                 # Утилиты
│   │   ├── __init__.py
│   │   ├── validators.py     # Валидация данных
│   │   ├── helpers.py        # Вспомогательные функции
│   │   └── logging.py        # Система логирования
│   ├── keyboards/             # Клавиатуры
│   │   ├── __init__.py
│   │   └── inline.py         # Inline клавиатуры
│   ├── constants/             # Константы (модульная структура)
│   │   ├── __init__.py
│   │   ├── config.py         # Константы конфигурации
│   │   └── errors.py         # Константы ошибок
│   ├── lexicon/               # Лексиконы (модульная структура)
│   │   ├── __init__.py
│   │   ├── start.py          # Лексикон для /start
│   │   ├── message.py        # Лексикон для сообщений
│   │   ├── callbacks.py      # Лексикон для callback-запросов
│   │   ├── keyboards.py      # Лексикон для клавиатур
│   │   ├── ai_providers.py   # Лексикон для AI провайдеров
│   │   └── utils.py          # Лексикон для утилит
│   ├── log_lexicon/           # Лог-лексиконы (модульная структура)
│   │   ├── __init__.py
│   │   ├── start.py          # Лог-лексикон для /start
│   │   ├── message.py        # Лог-лексикон для сообщений
│   │   ├── callbacks.py      # Лог-лексикон для callback-запросов
│   │   ├── keyboards.py      # Лог-лексикон для клавиатур
│   │   ├── ai_providers.py   # Лог-лексикон для AI провайдеров
│   │   └── utils.py          # Лог-лексикон для утилит
│   ├── constants.py           # Устаревший файл констант
│   ├── lexicon.py            # Устаревший файл лексикона
│   └── log_lexicon.py        # Устаревший файл лог-лексикона
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

### 3.1 Архитектура AI сервиса с несколькими провайдерами

**Система теперь поддерживает множественных AI провайдеров с автоматическим fallback:**

**Основные компоненты:**
- `AIManager` - центральный менеджер для управления несколькими провайдерами
- `BaseAIProvider` - абстрактный базовый класс для всех провайдеров
- `DeepSeekProvider` - провайдер для DeepSeek API
- `OpenRouterProvider` - провайдер для OpenRouter API
- `ResponseCache` - система кеширования ответов с поддержкой нескольких провайдеров
- `ConversationMessage` - структура для сообщений диалога
- `AIResponse` - структура ответа от AI

**Поддерживаемые провайдеры:**
1. **DeepSeek API** - основной провайдер
2. **OpenRouter API** - резервный провайдер с доступом к множественным моделям

**Особенности реализации:**
- Автоматический fallback между провайдерами
- Асинхронная работа с httpx клиентом
- Retry логика с экспоненциальной задержкой
- Обработка различных типов ошибок (401, 402, 429, 5xx)
- Кеширование ответов на основе MD5 хешей с учетом провайдера
- Мониторинг состояния через `health_check()` для всех провайдеров
- Статистика использования и fallback событий

### 3.2 Конфигурация AI сервиса

```
# Настройки DeepSeek API
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_MAX_TOKENS=1000
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_TIMEOUT=30

# Настройки OpenRouter API
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=anthropic/claude-3-haiku
OPENROUTER_MAX_TOKENS=1000
OPENROUTER_TEMPERATURE=0.8
OPENROUTER_TIMEOUT=60
OPENROUTER_SITE_URL=https://your-site.com
OPENROUTER_APP_NAME=AI-Assistant-Bot

# Настройки AI менеджера
AI_PRIMARY_PROVIDER=openrouter
AI_FALLBACK_PROVIDER=deepseek
AI_ENABLE_FALLBACK=true

# Настройки кеширования
CACHE_TTL=3600
```

### 3.3 Обработка ошибок и Fallback система

**Иерархия ошибок:**
- `AIProviderError` - базовый класс ошибок провайдеров
- `APIConnectionError` - ошибки подключения
- `APIRateLimitError` - превышение лимитов
- `APIAuthenticationError` - ошибки аутентификации
- `APIQuotaExceededError` - превышение квоты/недостаток средств

**Автоматическая Fallback стратегия:**
1. Попытка обращения к основному провайдеру (настраивается в AI_PRIMARY_PROVIDER)
2. При временных ошибках (сеть, rate limit) - автоматическое переключение на резервный провайдер
3. При критических ошибках (аутентификация, квота) - остановка без fallback
4. Логирование всех fallback событий для мониторинга
5. Статистика успешности провайдеров

**Стратегия обработки HTTP статусов:**
- `401` - Ошибка аутентификации (критическая)
- `402` - Недостаток средств (критическая)
- `429` - Rate limit (временная, retry с задержкой)
- `5xx` - Ошибки сервера (временная, retry)

При недоступности всех провайдеров система возвращает предзаданные эмпатичные ответы.

## 4. Базы данных

### 4.1 Схема базы данных

**Таблица users:**
```
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
```
CREATE TABLE conversations (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    message_text TEXT,
    response_text TEXT,
    role VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    ai_model VARCHAR(100),
    tokens_used INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);
```

### 4.2 Миграции базы данных

**Alembic миграции:**
- `alembic/env.py` - конфигурация среды миграций
- `alembic/versions/` - директория с файлами миграций
- `alembic.ini` - конфигурационный файл Alembic

**Команды миграций:**
```bash
# Создание новой миграции
alembic revision --autogenerate -m "Описание изменений"

# Применение миграций
alembic upgrade head

# Откат миграций
alembic downgrade -1
```

## 5. Модульная структура лексиконов и констант

### 5.1 Лексиконы

Для улучшения поддерживаемости кода все текстовые сообщения были разделены на модульные лексиконы:

- `app/lexicon/start.py` - сообщения для обработчика команды /start
- `app/lexicon/message.py` - сообщения для обработчика текстовых сообщений
- `app/lexicon/callbacks.py` - сообщения для обработчика callback-запросов

### 5.2 Константы

Константы также были разделены на модульные файлы:

- `app/constants/config.py` - константы и сообщения об ошибках конфигурации
- `app/constants/errors.py` - общие сообщения об ошибках

### 5.3 Лог-лексиконы

Сообщения для логирования были разделены на модульные файлы:

- `app/log_lexicon/start.py` - лог-сообщения для обработчика команды /start
- `app/log_lexicon/message.py` - лог-сообщения для обработчика текстовых сообщений
- `app/log_lexicon/callbacks.py` - лог-сообщения для обработчика callback-запросов

Старые файлы (`app/lexicon.py`, `app/constants.py`, `app/log_lexicon.py`) помечены как устаревшие и будут удалены в следующих версиях.

## 6. Тестирование

### 6.1 Структура тестов

```
tests/
├── __init__.py
├── conftest.py              # Конфигурация pytest
├── unit/                    # Модульные тесты
│   ├── __init__.py
│   ├── test_config.py      # Тесты конфигурации
│   ├── test_models.py      # Тесты моделей
│   └── test_base_ai_provider.py  # Тесты базового AI провайдера
├── integration/             # Интеграционные тесты
│   ├── __init__.py
│   ├── test_database.py    # Тесты базы данных
│   ├── test_ai_service.py  # Тесты AI сервиса
│   ├── test_deepseek_provider.py  # Тесты DeepSeek провайдера
│   ├── test_openrouter_provider.py  # Тесты OpenRouter провайдера
│   ├── test_ai_manager.py  # Тесты AI менеджера
│   └── test_message_handler.py  # Тесты обработчика сообщений
└── fixtures/                # Фикстуры для тестов
    ├── __init__.py
    └── test_data.json      # Тестовые данные
```

### 6.2 Команды тестирования

```bash
# Запуск всех тестов
pytest

# Запуск с покрытием кода
pytest --cov=app --cov-report=html

# Запуск конкретного теста
pytest tests/unit/test_config.py

# Запуск тестов с подробным выводом
pytest -v
```

## 7. Развертывание

### 7.1 Docker

**Dockerfile:**
```
FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY pyproject.toml .
RUN pip install uv && uv pip install --system -r pyproject.toml

# Копирование кода
COPY . .

# Создание пользователя
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Порты и команды
EXPOSE 8000
CMD ["python", "main.py"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  ai-assist:
    build: .
    ports:
      - "8000:8000"
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - DATABASE_URL=${DATABASE_URL}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    depends_on:
      - postgres
    volumes:
      - ./logs:/app/logs

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ai_assist
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### 7.2 Команды развертывания

```bash
# Сборка и запуск с Docker
docker-compose up -d

# Остановка сервисов
docker-compose down

# Просмотр логов
docker-compose logs -f ai-assist
```
```

```
