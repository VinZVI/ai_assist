# Docker документация для AI-Компаньон

## 🐳 Описание

Этот проект использует Docker Compose для оркестрации контейнеров. Конфигурация включает:

- **PostgreSQL** - основная база данных
- **Redis** - кэш и очереди задач
- **AI-Компаньон** - основное приложение (Telegram бот)

## 📦 Переменные окружения

### Обязательные переменные

```env
# PostgreSQL
POSTGRES_DB=ai_assist
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here

# Redis
REDIS_PASSWORD=redis_password

# Telegram Bot (обязательно!)
BOT_TOKEN=your_bot_token_here

# OpenRouter API (обязательно!)
OPENROUTER_API_KEY=your_api_key_here

# Application Security
SECRET_KEY=your_very_secure_secret_key_here_minimum_32_characters

# Admin Configuration
ADMIN_USER_ID=your_telegram_user_id
```

## Troubleshooting

### Проблемы с подключением к БД

Если приложение не может подключиться к базе данных:

1. Проверьте, что контейнеры запущены:
   ```bash
   docker-compose ps
   ```

2. Проверьте логи базы данных:
   ```bash
   docker-compose logs postgres
   ```

3. Убедитесь, что переменные окружения установлены правильно

### Проблемы с Redis

Если приложение не может подключиться к Redis:

1. Проверьте логи Redis:
   ```bash
   docker-compose logs redis
   ```

2. Убедитесь, что пароль Redis установлен правильно

### Проблемы с Telegram Bot

Если бот не отвечает:

1. Проверьте логи приложения:
   ```bash
   docker-compose logs app
   ```

2. Убедитесь, что BOT_TOKEN установлен правильно

### Проблемы с OpenRouter API

Если AI не отвечает:

1. Проверьте логи приложения:
   ```bash
   docker-compose logs app
   ```

2. Убедитесь, что OPENROUTER_API_KEY установлен правильно

## 🛠️ Команды Docker Compose

### Запуск всего стека
```bash
docker-compose up -d
```

### Остановка всего стека
```bash
docker-compose down
```

### Просмотр логов
```bash
docker-compose logs -f
```

### Пересборка приложения
```bash
docker-compose build --no-cache
```

### Обновление приложения
```bash
docker-compose pull
docker-compose up -d
```

## 📊 Мониторинг

### Проверка статуса контейнеров
```bash
docker-compose ps
```

### Проверка использования ресурсов
```bash
docker stats
```

## 🔧 Разработка

### Монтирование кода для разработки
В режиме разработки код монтируется в контейнер, что позволяет изменять код без пересборки образа.

### Отладка
Для отладки можно подключиться к контейнеру:
```bash
docker-compose exec app bash
```

## 🔄 CI/CD

### Автоматическая сборка
GitHub Actions автоматически собирает и пушит образы в Docker Hub при коммитах в main ветку.

### Ручная сборка
```bash
docker build -t ai-assistant-bot .
```

## 🔐 Безопасность

### Рекомендации
1. Используйте сильные пароли
2. Не коммитьте .env файлы
3. Регулярно обновляйте образы
4. Используйте сети Docker для изоляции

### Сканирование уязвимостей
```bash
docker scan ai-assistant-bot
```