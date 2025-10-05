# 🚀 Deployment Guide

## 📋 Подготовка к продакшену

### Требования к серверу

- **Операционная система**: Ubuntu 20.04+ или аналогичная Linux система
- **RAM**: Минимум 2GB (рекомендуется 4GB+)
- **Диск**: Минимум 10GB свободного места
- **Docker**: Версия 20.10+
- **Docker Compose**: Версия 1.29+

### Системные зависимости

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

## 🛠️ Настройка окружения

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd ai_assist
```

### 2. Создание файлов конфигурации

```bash
# Создание файла конфигурации для Docker
cp .env.docker.example .env.docker

# Создание файла конфигурации для продакшена
cp .env.production.example .env.production
```

### 3. Настройка переменных окружения

Отредактируйте файлы `.env.docker` и `.env.production`, заполнив реальными значениями:

```bash
# Пример .env.docker
DATABASE_NAME=ai_assist
DATABASE_USER=postgres
DATABASE_PASSWORD=your_secure_password_here
REDIS_PASSWORD=your_redis_password_here
BOT_TOKEN=your_bot_token_from_botfather
DEEPSEEK_API_KEY=your_deepseek_api_key
SECRET_KEY=your_very_secure_secret_key_here_minimum_32_characters
ADMIN_USER_ID=your_telegram_user_id
```

## 🚢 Деплой приложения

### Вариант 1: Docker Compose (рекомендуется)

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр статуса контейнеров
docker-compose ps

# Просмотр логов
docker-compose logs -f
```

### Вариант 2: Docker Compose с веб-сервером (webhook режим)

```bash
# Запуск с веб-сервером для webhook
docker-compose -f docker-compose.yml -f docker-compose.web.yml up -d

# Просмотр статуса контейнеров
docker-compose -f docker-compose.yml -f docker-compose.web.yml ps
```

### Вариант 3: Использование deployment скрипта

```bash
# Развертывание приложения
./scripts/deploy.sh deploy

# Просмотр логов
./scripts/deploy.sh logs
```

## 🔧 Настройка webhook

Если вы используете webhook режим:

1. Установите домен или IP адрес вашего сервера
2. Настройте SSL сертификат (рекомендуется Let's Encrypt)
3. Установите webhook URL через BotFather или API:

```bash
# Пример установки webhook через curl
curl -F "url=https://your-domain.com/webhook" https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook
```

## 📊 Мониторинг

### Проверка состояния приложения

```bash
# Healthcheck через Docker
docker-compose exec ai_assist_bot python -c "from app.config import get_config; print('Config loaded successfully')"

# Healthcheck через HTTP (если используется веб-сервер)
curl http://localhost:8080/health
```

### Просмотр логов

```bash
# Логи бота
docker-compose logs ai_assist_bot

# Логи базы данных
docker-compose logs postgres

# Логи Redis
docker-compose logs redis

# Все логи
docker-compose logs -f
```

## 🔒 Безопасность

### Рекомендации по безопасности

1. **Используйте сложные пароли**:
   - Минимум 16 символов для паролей БД
   - Минимум 32 символа для SECRET_KEY

2. **Не храните секреты в репозитории**:
   - Все файлы `.env` добавлены в `.gitignore`
   - Используйте внешние secret managers в продакшене

3. **Обновляйте зависимости регулярно**:
   ```bash
   # Проверка уязвимостей
   pip install safety
   safety check
   ```

4. **Ограничьте доступ к портам**:
   - Используйте firewall (ufw, iptables)
   - Открывайте только необходимые порты

### Настройка SSL (рекомендуется)

```bash
# Установка Certbot
sudo apt install certbot

# Получение сертификата
sudo certbot certonly --standalone -d your-domain.com

# Обновление конфигурации Nginx
# (обновите nginx.conf для использования SSL)
```

## 🔄 Обновление приложения

### Автоматическое обновление через GitHub Actions

1. Настройте secrets в репозитории GitHub
2. Push изменений в ветку `main`
3. CI/CD pipeline автоматически:
   - Запустит тесты
   - Соберет Docker образ
   - Запушит образ в Docker Hub
   - Задеплоит на сервер

### Ручное обновление

```bash
# Остановка сервисов
docker-compose down

# Получение последних изменений
git pull

# Пересборка образов
docker-compose build

# Запуск сервисов
docker-compose up -d
```

## 🚨 Устранение неполадок

### Частые проблемы и их решения

1. **Контейнеры не запускаются**:
   ```bash
   # Проверка логов
   docker-compose logs
   
   # Проверка конфигурации
   docker-compose config
   ```

2. **Ошибки подключения к базе данных**:
   ```bash
   # Проверка статуса PostgreSQL
   docker-compose exec postgres pg_isready
   
   # Проверка переменных окружения
   docker-compose exec ai_assist_bot env
   ```

3. **Ошибки webhook**:
   ```bash
   # Проверка webhook статуса
   curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
   ```

4. **Проблемы с AI провайдерами**:
   ```bash
   # Проверка API ключей
   docker-compose exec ai_assist_bot python scripts/diagnostics/check_api_connectivity.py
   ```

## 📈 Масштабирование

### Горизонтальное масштабирование

Для увеличения производительности можно:

1. **Увеличить количество worker'ов**:
   ```yaml
   # docker-compose.override.yml
   services:
     ai_assist_bot:
       deploy:
         replicas: 3
   ```

2. **Использовать внешние сервисы**:
   - Внешняя PostgreSQL база данных
   - Внешний Redis кластер
   - Load balancer

3. **Мониторинг и алертинг**:
   - Интеграция с Prometheus и Grafana
   - Настройка Sentry для отслеживания ошибок
   - Настройка alerting через email или Slack

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи приложения
2. Убедитесь, что все переменные окружения установлены правильно
3. Проверьте подключение к внешним сервисам (БД, Redis, AI API)
4. Обратитесь к документации или создайте issue в репозитории