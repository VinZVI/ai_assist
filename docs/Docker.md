# 🐳 Docker инструкции для AI-Компаньон

## Быстрый запуск для разработки

### ⚠️ ВАЖНО: Настройка безопасности

Перед запуском создайте файл `.env.docker` с вашими реальными паролями:

```bash
# Скопируйте шаблон
cp .env.docker.example .env.docker

# Отредактируйте файл и замените все пароли на безопасные!
nano .env.docker
```

**Обязательно измените следующие значения:**
- `DATABASE_PASSWORD` - безопасный пароль для PostgreSQL
- `REDIS_PASSWORD` - безопасный пароль для Redis
- `BOT_TOKEN` - ваш токен от @BotFather
- `DEEPSEEK_API_KEY` - ваш API ключ от DeepSeek
- `SECRET_KEY` - случайная строка для подписи данных

### 1. Запуск только PostgreSQL и Redis
```bash
# Запуск базы данных и кеша
docker-compose up postgres redis -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs postgres redis
```

### 2. Запуск с Adminer (веб-интерфейс для БД)
```bash
# Запуск с интерфейсом управления БД
docker-compose --profile development up -d

# Adminer будет доступен на http://localhost:8080
# Сервер: postgres
# Пользователь: postgres
# Пароль: 3245
# База данных: ai_assist
```

### 3. Локальная разработка (рекомендуется)
```bash
# Запуск только инфраструктуры
docker-compose up postgres redis -d

# Запуск бота локально
python main.py
```

## Продакшен

### Полный запуск с ботом в контейнере
```bash
# Создание .env файла с реальными токенами
cp .env.example .env
# Отредактируйте .env файл!

# Сборка и запуск всего
docker-compose --profile production up -d

# Просмотр логов
docker-compose logs -f ai_assist_bot
```

## Управление

### Остановка сервисов
```bash
# Остановка всех сервисов
docker-compose down

# Остановка с удалением volumes (ВНИМАНИЕ: все данные будут потеряны!)
docker-compose down -v
```

### Обновление образов
```bash
# Пересборка образа бота
docker-compose build ai_assist_bot

# Обновление всех образов
docker-compose pull
```

### Бэкап и восстановление
```bash
# Бэкап базы данных
docker-compose exec postgres pg_dump -U postgres -d ai_assist > backup.sql

# Восстановление
docker-compose exec -T postgres psql -U postgres -d ai_assist < backup.sql
```

## Мониторинг

### Просмотр ресурсов
```bash
# Использование ресурсов
docker stats

# Использование места
docker system df
```

### Логи
```bash
# Логи всех сервисов
docker-compose logs

# Логи конкретного сервиса
docker-compose logs ai_assist_bot

# Следить за логами в реальном времени
docker-compose logs -f
```

## Отладка

### Подключение к контейнерам
```bash
# Подключение к PostgreSQL
docker-compose exec postgres psql -U postgres -d ai_assist

# Подключение к Redis
docker-compose exec redis redis-cli

# Подключение к контейнеру бота
docker-compose exec ai_assist_bot bash
```

### Проверка здоровья
```bash
# Проверка статуса healthcheck
docker-compose ps

# Детальная информация
docker inspect ai_assist_postgres | grep Health -A 10
```

## Переменные окружения

Основные переменные для Docker окружения:

```env
# База данных (автоматически настраивается для Docker)
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=ai_assist
DATABASE_USER=postgres
DATABASE_PASSWORD=3245

# Redis (автоматически настраивается для Docker)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis_password

# Telegram Bot (обязательно!)
BOT_TOKEN=your_bot_token_here

# DeepSeek API (обязательно!)
DEEPSEEK_API_KEY=your_api_key_here
```

## Troubleshooting

### Проблемы с подключением к БД
```bash
# Проверка сетевого подключения
docker-compose exec ai_assist_bot ping postgres

# Проверка портов
docker-compose port postgres 5432
```

### Очистка системы
```bash
# Удаление неиспользуемых ресурсов
docker system prune

# Полная очистка (ВНИМАНИЕ!)
docker system prune -a --volumes
```

### Пересоздание с нуля
```bash
# Полная остановка и удаление
docker-compose down -v --remove-orphans

# Удаление образов
docker-compose down --rmi all

# Запуск заново
docker-compose up -d
```