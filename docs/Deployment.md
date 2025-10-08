# Документация по деплою AI-Компаньон

## 🚀 Подготовка к деплою

### Требования к серверу

- Ubuntu 20.04+ или аналогичная Linux система
- 2 CPU cores
- 4GB RAM (рекомендуется 8GB)
- 20GB SSD (рекомендуется 50GB)
- Доступ к интернету
- Открытые порты: 22 (SSH), 80 (HTTP), 443 (HTTPS)

### Необходимые сервисы

- **PostgreSQL 13+** - основная база данных
- **Redis 6+** - кэш и очереди задач
- **Docker & Docker Compose** - контейнеризация
- **Nginx** - reverse proxy (опционально)
- **Let's Encrypt** - SSL сертификаты (опционально)

## 📦 Подготовка окружения

### 1. Установка Docker

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
```

### 2. Подготовка директории

```bash
# Создание рабочей директории
mkdir -p /opt/ai-assistant
cd /opt/ai-assistant

# Клонирование репозитория
git clone https://github.com/yourusername/ai-assistant.git .
```

## ⚙️ Конфигурация

### Обязательные переменные окружения

Создайте файл `.env` в корне проекта:

```env
# PostgreSQL
POSTGRES_DB=ai_assist
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here

# Redis
REDIS_PASSWORD=your_redis_password_here

# Telegram Bot
BOT_TOKEN=your_bot_token_from_botfather

# OpenRouter API
OPENROUTER_API_KEY=your_openrouter_api_key

# Application Security
SECRET_KEY=your_very_secure_secret_key_here_minimum_32_characters

# Admin Configuration
ADMIN_USER_ID=your_telegram_user_id

# Database URL (автоматически генерируется из вышеуказанных параметров)
DATABASE_URL=postgresql+asyncpg://postgres:your_secure_password_here@postgres:5432/ai_assist

# User Limits
FREE_MESSAGES_LIMIT=10
PREMIUM_PRICE=99
```

## 🐳 Деплой с Docker Compose

### 1. Запуск стека

```bash
# Запуск в фоновом режиме
docker-compose up -d

# Проверка статуса контейнеров
docker-compose ps
```

### 2. Инициализация базы данных

```bash
# Запуск миграций
docker-compose exec app alembic upgrade head

# Создание администратора (опционально)
docker-compose exec app python scripts/create_admin.py
```

### 3. Проверка работоспособности

```bash
# Просмотр логов
docker-compose logs -f

# Проверка API подключения
docker-compose exec app python scripts/diagnostics/check_api_connectivity.py
```

## 🔧 Управление приложением

### Обновление приложения

```bash
# Остановка приложения
docker-compose down

# Получение последних изменений
git pull

# Пересборка образов
docker-compose build --no-cache

# Запуск обновленного приложения
docker-compose up -d
```

### Масштабирование

Для высоконагруженных систем можно масштабировать отдельные сервисы:

```bash
# Масштабирование приложения
docker-compose up -d --scale app=3
```

### Резервное копирование

```bash
# Бэкап базы данных
docker-compose exec postgres pg_dump -U postgres ai_assist > backup_$(date +%Y%m%d).sql

# Восстановление базы данных
docker-compose exec -T postgres psql -U postgres ai_assist < backup_*.sql
```

## 🛡️ Безопасность

### Рекомендации по безопасности

1. **Изоляция сетей**: Используйте Docker сети для изоляции сервисов
2. **Секреты**: Не храните секреты в коде, используйте переменные окружения
3. **Обновления**: Регулярно обновляйте Docker образы
4. **Мониторинг**: Настройте мониторинг и alerting

### Сканирование уязвимостей

```bash
# Сканирование Docker образа
docker scan ai-assistant_app
```

## 📊 Мониторинг и логирование

### Просмотр логов

```bash
# Все логи
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f app

# Логи за последние 10 минут
docker-compose logs --since 10m
```

### Метрики

Для мониторинга можно использовать:
- **Prometheus** + **Grafana** для метрик
- **ELK Stack** для логирования
- **Health checks** для проверки состояния

## 🔧 Troubleshooting

### Частые проблемы

#### 1. Приложение не запускается

Проверьте логи:
```bash
docker-compose logs app
```

Убедитесь, что все переменные окружения установлены правильно.

#### 2. Проблемы с подключением к БД

Проверьте логи базы данных:
```bash
docker-compose logs postgres
```

Убедитесь, что параметры подключения указаны правильно в .env файле.

#### 3. Проблемы с OpenRouter API

Проверьте API ключ и подключение:
```bash
docker-compose exec app python scripts/diagnostics/check_api_connectivity.py
```

#### 4. Проблемы с Telegram ботом

Проверьте BOT_TOKEN и убедитесь, что вебхук не конфликтует:
```bash
docker-compose exec app python scripts/clear_webhook.py
```

## 🔄 CI/CD

### GitHub Actions

Проект включает workflow для автоматического деплоя:

1. **Build and Test** - сборка и тестирование при каждом пуше
2. **Deploy** - автоматический деплой при пуше в main ветку

### Ручной деплой

Для ручного деплоя используйте:

```bash
# Сборка образов
docker-compose build

# Запуск
docker-compose up -d

# Проверка
docker-compose ps
```

## 📈 Производительность

### Рекомендации по оптимизации

1. **Кэширование**: Используйте Redis для кэширования частых запросов
2. **Индексы БД**: Убедитесь, что все необходимые индексы созданы
3. **Асинхронность**: Используйте асинхронные операции где возможно
4. **Пул соединений**: Настройте пул соединений к БД

### Мониторинг производительности

```bash
# Мониторинг ресурсов
docker stats

# Профилирование приложения
docker-compose exec app python -m cProfile -o profile.out main.py
```

## 🆘 Поддержка

### Получение помощи

1. **Документация**: Проверьте все .md файлы в папке docs/
2. **Issues**: Создайте issue в GitHub репозитории
3. **Логи**: Приложите логи при создании issue
4. **Community**: Присоединяйтесь к сообществу разработчиков

### Восстановление после сбоев

```bash
# Перезапуск всех сервисов
docker-compose restart

# Перезапуск конкретного сервиса
docker-compose restart app

# Полная пересборка
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📅 План обслуживания

### Еженедельные задачи

- [ ] Проверка логов на ошибки
- [ ] Обновление Docker образов
- [ ] Резервное копирование БД

### Ежемесячные задачи

- [ ] Аудит безопасности
- [ ] Оптимизация базы данных
- [ ] Обновление зависимостей

### Ежеквартальные задачи

- [ ] Полный аудит системы
- [ ] Тестирование disaster recovery плана
- [ ] Обновление документации