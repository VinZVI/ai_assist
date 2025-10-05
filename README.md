# 🤖 AI-Компаньон

> Telegram-бот для эмоциональной поддержки с интеграцией DeepSeek API

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.22+-green.svg)](https://aiogram.dev)
[![uv](https://img.shields.io/badge/uv-latest-orange.svg)](https://docs.astral.sh/uv/)

## 📋 Описание

AI-Компаньон - это Telegram-бот, предназначенный для предоставления эмоциональной поддержки и психологического комфорта пользователям. Бот использует искусственный интеллект от DeepSeek для генерации персонализированных ответов и поддержания естественного диалога.

### ✨ Основные функции

- 💬 **Умные диалоги** - Естественное общение с ИИ
- 🎯 **Эмоциональная поддержка** - Помощь в сложных ситуациях
- 💎 **Премиум функции** - Безлимитные сообщения за донат
- 📊 **Аналитика** - Отслеживание использования
- 🔒 **Безопасность** - Защита персональных данных

## 🚀 Быстрый старт

### Требования

- Python 3.11+
- PostgreSQL 13+
- uv (для управления зависимостями)

### Установка

1. **Клонируйте репозиторий**
   ```bash
   git clone <repository-url>
   cd ai_assist
   ```

2. **Установите зависимости через uv**
   ```bash
   uv sync
   ```

3. **Настройте переменные окружения**
   ```bash
   cp .env.example .env
   # Отредактируйте .env файл с вашими настройками
   ```

4. **Запустите миграции БД**
   ```bash
   uv run alembic upgrade head
   ```

5. **Запустите бота**
   ```bash
   uv run python app/main.py
   ```

## 🏗️ Архитектура

```

```


```

## 🚀 Деплой

### Требования к серверу
- Docker и Docker Compose
- Доступ к интернету
- Открытые порты (5432 для PostgreSQL, 6379 для Redis, 8000 для webhook)

### Подготовка к деплою

1. **Скопируйте файлы конфигурации**
   ```bash
   cp .env.docker.example .env.docker
   cp .env.production.example .env.production
   ```

2. **Отредактируйте переменные окружения**
   Заполните все переменные в `.env.docker` и `.env.production` реальными значениями

3. **Настройте webhook (опционально)**
   Если используете webhook, укажите `WEBHOOK_URL` и `WEBHOOK_SECRET`

Подробное руководство по деплою смотрите в [docs/Deployment.md](docs/Deployment.md)

### Деплой через Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f --tail=50

# Остановка сервисов
docker-compose down
```

### Деплой через скрипт

```bash
# Развертывание приложения
./scripts/deploy.sh deploy

# Просмотр логов
./scripts/deploy.sh logs

# Перезапустить приложение
./scripts/deploy.sh restart
```

### Деплой через GitHub Actions

1. Настройте secrets в репозитории:
   - `DOCKERHUB_USERNAME` - имя пользователя Docker Hub
   - `DOCKERHUB_TOKEN` - токен доступа к Docker Hub
   - `SERVER_HOST` - IP адрес сервера
   - `SERVER_USERNAME` - имя пользователя на сервере
   - `SERVER_SSH_KEY` - приватный SSH ключ для доступа к серверу

2. Push в ветку `main` автоматически запустит CI/CD pipeline

## 🔒 Безопасность
