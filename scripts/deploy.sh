#!/bin/bash

# AI-Компаньон Deployment Script
# ==============================================
# Скрипт для развертывания бота на сервере

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
    exit 1
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    error "Не запускайте этот скрипт от имени root"
fi

# Check dependencies
check_dependencies() {
    log "Проверка зависимостей..."
    
    command -v docker >/dev/null 2>&1 || error "Docker не установлен"
    command -v docker-compose >/dev/null 2>&1 || warn "docker-compose не установлен, пробуем docker compose"
    
    log "Все зависимости установлены"
}

# Create necessary directories
create_directories() {
    log "Создание директорий..."
    
    mkdir -p ./logs
    mkdir -p ./init-db
    
    log "Директории созданы"
}

# Setup environment files
setup_environment() {
    log "Настройка переменных окружения..."
    
    if [ ! -f ".env.production" ]; then
        error "Файл .env.production не найден. Скопируйте .env.production.example и заполните его."
    fi
    
    log "Переменные окружения настроены"
}

# Pull latest images
pull_images() {
    log "Получение последних образов..."
    
    if command -v docker-compose >/dev/null 2>&1; then
        docker-compose pull
    else
        docker compose pull
    fi
    
    log "Образы обновлены"
}

# Stop existing containers
stop_containers() {
    log "Остановка существующих контейнеров..."
    
    if command -v docker-compose >/dev/null 2>&1; then
        docker-compose down
    else
        docker compose down
    fi
    
    log "Контейнеры остановлены"
}

# Start containers
start_containers() {
    log "Запуск контейнеров..."
    
    if command -v docker-compose >/dev/null 2>&1; then
        docker-compose up -d
    else
        docker compose up -d
    fi
    
    log "Контейнеры запущены"
}

# Check container health
check_health() {
    log "Проверка состояния контейнеров..."
    
    sleep 10  # Wait for containers to start
    
    if command -v docker-compose >/dev/null 2>&1; then
        docker-compose ps
    else
        docker compose ps
    fi
    
    log "Проверка завершена"
}

# Show logs
show_logs() {
    log "Показ логов (нажмите Ctrl+C для выхода)..."
    
    if command -v docker-compose >/dev/null 2>&1; then
        docker-compose logs -f --tail=50
    else
        docker compose logs -f --tail=50
    fi
}

# Main deployment function
deploy() {
    log "Начало развертывания AI-Компаньон..."
    
    check_dependencies
    create_directories
    setup_environment
    pull_images
    stop_containers
    start_containers
    check_health
    
    log "Развертывание завершено успешно!"
    log "Для просмотра логов выполните: ./scripts/deploy.sh logs"
}

# Main script logic
case "$1" in
    deploy)
        deploy
        ;;
    logs)
        show_logs
        ;;
    restart)
        stop_containers
        start_containers
        check_health
        ;;
    status)
        if command -v docker-compose >/dev/null 2>&1; then
            docker-compose ps
        else
            docker compose ps
        fi
        ;;
    *)
        echo "Использование: $0 {deploy|logs|restart|status}"
        echo ""
        echo "Команды:"
        echo "  deploy   - Развернуть приложение"
        echo "  logs     - Показать логи"
        echo "  restart  - Перезапустить приложение"
        echo "  status   - Показать статус контейнеров"
        exit 1
        ;;
esac