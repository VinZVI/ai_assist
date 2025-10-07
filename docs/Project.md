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
│   │   └── health.py         # Healthcheck endpoint
│   ├── services/              # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── ai_manager.py     # Менеджер AI провайдеров
│   │   ├── conversation_service.py # Сервис работы с диалогами
│   │   ├── user_service.py   # Логика пользователей
│   │   └── ai_providers/     # Провайдеры AI
│   │       ├── __init__.py
│   │       ├── base.py       # Базовый класс провайдера
│   │       ├── deepseek.py   # DeepSeek провайдер
│   │       └── openrouter.py # OpenRouter провайдер
│   ├── utils/                 # Утилиты
│   │   ├── __init__.py
│   │   └── logging.py        # Система логирования
│   ├── keyboards/             # Клавиатуры
│   │   └── __init__.py       # Inline клавиатуры
│   ├── constants/             # Константы (модульная структура)
│   │   ├── __init__.py
│   │   ├── config.py         # Константы конфигурации
│   │   └── errors.py         # Константы ошибок
│   ├── lexicon/               # Лексиконы (модульная структура)
│   │   ├── __init__.py
│   │   ├── gettext.py        # Функции локализации
│   │   ├── ru.py             # Русский лексикон
│   │   └── en.py             # Английский лексикон
│   └── log_lexicon/           # Лог-лексиконы (модульная структура)
│       ├── __init__.py
│       ├── en.py             # Английский лог-лексикон (словарная структура)
│       └── ru.py             # Русский лог-лексикон (словарная структура)
├── tests/                      # Тесты приложения
│   ├── __init__.py            # Инициализация пакета тестов
│   ├── conftest.py           # Конфигурация pytest
│   ├── fixtures/             # Фикстуры для тестов
│   ├── unit/                 # Модульные тесты
│   └── integration/          # Интеграционные тесты
├── scripts/                    # Скрипты диагностики
│   ├── __init__.py
│   ├── checks/               # Скрипты проверки
│   └── diagnostics/          # Диагностические скрипты
├── docs/                      # Документация
│   ├── Project.md            # Описание проекта (этот файл)
│   ├── Tasktracker.md        # Отслеживание задач
│   ├── Diary.md              # Дневник разработки
│   ├── Testing.md            # Документация по тестированию
│   ├── Deployment.md         # Документация по деплою
│   ├── Docker.md             # Документация по Docker
│   ├── qa.md                 # Вопросы и ответы
│   └── changelog.md          # Журнал изменений
├── alembic/                    # Миграции базы данных
├── logs/                       # Логи приложения
├── .github/                    # GitHub Actions workflows
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

Все сообщения для логирования были консолидированы в двух основных файлах для упрощения структуры и улучшения поддерживаемости:

- `app/log_lexicon/en.py` - английский лог-лексикон (словарная структура)
- `app/log_lexicon/ru.py` - русский лог-лексикон (словарная структура)

Старые файлы (`app/log_lexicon/main.py`, `app/log_lexicon/start.py`, `app/log_lexicon/message.py`, `app/log_lexicon/callbacks.py`, `app/log_lexicon/database.py`, `app/log_lexicon/config.py`) были удалены в рамках рефакторинга системы лог-лексиконов.

## 6. Тестирование

### 6.1 Структура тестов

```
tests/
├── __init__.py
├── conftest.py              # Конфигурация pytest
├── fixtures/             # Фикстуры для тестов
├── unit/                 # Модульные тесты
└── integration/          # Интеграционные тесты
```

### 6.2 Команды тестирования

```
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

```
# Сборка и запуск с Docker
docker-compose up -d
```

## 4. CI/CD Pipeline

### GitHub Actions Workflows

Проект использует GitHub Actions для автоматизации процессов CI/CD:

1. **CI Workflow** (`ci.yml`) - Непрерывная интеграция
   - Запуск тестов на Python 3.11 и 3.12
   - Проверка качества кода (linting)
   - Статическая типизация (mypy)
   - Форматирование кода (ruff)

2. **CD Workflow** (`cd.yml`) - Непрерывная доставка
   - Сборка Docker образов
   - Пуш в Docker Hub
   - Деплой на сервер через SSH

3. **Security Workflow** (`security.yml`) - Сканирование безопасности
   - Проверка уязвимостей в коде (Bandit)
   - Анализ зависимостей (Safety)

4. **Documentation Workflow** (`docs.yml`) - Генерация документации
   - Сборка и деплой документации на GitHub Pages

### Secrets Configuration

Для работы CD pipeline необходимо настроить следующие secrets в репозитории:

- `DOCKERHUB_USERNAME` - имя пользователя Docker Hub
- `DOCKERHUB_TOKEN` - токен доступа к Docker Hub
- `SERVER_HOST` - IP адрес сервера
- `SERVER_USERNAME` - имя пользователя на сервере
- `SERVER_SSH_KEY` - приватный SSH ключ для доступа к серверу

### Environment Files

- `.env.example` - шаблон для локальной разработки
- `.env.docker.example` - шаблон для Docker окружения
- `.env.production.example` - шаблон для продакшена

## 5. Деплой и развертывание

Подробное руководство по деплою смотрите в [Deployment.md](Deployment.md)

### Поддерживаемые режимы развертывания

1. **Polling режим** - стандартный режим с периодическим опросом Telegram API
2. **Webhook режим** - более эффективный режим с webhook callback'ами от Telegram
3. **Docker Compose** - контейнеризированное развертывание всех сервисов
4. **Kubernetes** - оркестрация контейнеров (планируется)

### Требования к серверу

- **Операционная система**: Ubuntu 20.04+ или аналогичная Linux система
- **RAM**: Минимум 2GB (рекомендуется 4GB+)
- **Диск**: Минимум 10GB свободного места
- **Docker**: Версия 20.10+
- **Docker Compose**: Версия 1.29+

## 6. Мониторинг и логирование

### Логирование

Приложение использует `loguru` для структурированного логирования:

- Консольный вывод с эмодзи и цветами
- Файловый вывод в формате JSON
- Отдельные файлы для ошибок
- Настраиваемый уровень логирования

### Метрики

Планируется интеграция с системами мониторинга:
- Prometheus для сбора метрик
- Grafana для визуализации
- Sentry для отслеживания ошибок

## 7. Безопасность

### Защита данных

- Шифрование данных в базе данных
- Использование HTTPS для всех сетевых запросов
- Регулярное обновление зависимостей и системы

### Авторизация и аутентификация

- Использование токенов для аутентификации API
- Многофакторная аутентификация для администраторов

### Безопасность кода

- Регулярное использование инструментов анализа кода (Bandit, Safety)
- Обновление инструментов и библиотек
