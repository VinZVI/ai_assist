#!/bin/bash

# AI-Компаньон Web Server Startup Script
# ==============================================
# Скрипт для запуска веб-сервера

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
    
    command -v python >/dev/null 2>&1 || error "Python не установлен"
    command -v uv >/dev/null 2>&1 || error "uv не установлен"
    
    log "Все зависимости установлены"
}

# Install dependencies
install_dependencies() {
    log "Установка зависимостей..."
    
    uv sync
    
    log "Зависимости установлены"
}

# Start web server
start_server() {
    log "Запуск веб-сервера..."
    
    uv run python -m app.web
    
    log "Веб-сервер запущен"
}

# Main script logic
case "$1" in
    start)
        check_dependencies
        install_dependencies
        start_server
        ;;
    install)
        install_dependencies
        ;;
    *)
        echo "Использование: $0 {start|install}"
        echo ""
        echo "Команды:"
        echo "  start    - Установить зависимости и запустить веб-сервер"
        echo "  install  - Установить зависимости"
        exit 1
        ;;
esac