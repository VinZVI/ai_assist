@echo off
REM AI-Компаньон Web Server Startup Script
REM ==============================================
REM Скрипт для запуска веб-сервера на Windows

setlocal

echo [%date% %time%] Проверка зависимостей...

REM Check if uv is installed
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: uv не установлен
    exit /b 1
)

echo [%date% %time%] Установка зависимостей...
uv sync
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: Не удалось установить зависимости
    exit /b 1
)

echo [%date% %time%] Запуск веб-сервера...
uv run python -m app.web

echo [%date% %time%] Веб-сервер остановлен