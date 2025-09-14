#!/bin/bash
set -e

# Скрипт инициализации PostgreSQL для AI-Компаньон

echo "🔧 Инициализация базы данных AI-Компаньон..."

# Создание базы данных если она не существует
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Создаем расширения
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
    
    -- Настройки для оптимизации
    ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
    ALTER SYSTEM SET log_statement = 'all';
    ALTER SYSTEM SET log_min_duration_statement = 1000;
    
    -- Создаем пользователя для приложения (если нужно)
    -- CREATE USER ai_assist_user WITH PASSWORD 'secure_password';
    -- GRANT ALL PRIVILEGES ON DATABASE ai_assist TO ai_assist_user;
EOSQL

echo "✅ База данных AI-Компаньон инициализирована!"