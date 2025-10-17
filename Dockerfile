# Используем официальный Python образ
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем uv для управления зависимостями
RUN pip install uv

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости
RUN uv sync --frozen

# Копируем исходный код приложения
COPY app/ ./app/
COPY main.py ./
COPY alembic.ini ./
COPY alembic/ ./alembic/

# Создаем директорию для логов
RUN mkdir -p /app/logs

# Создаем непривилегированного пользователя
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Экспонируем порты (8000 для webhook, 8080 для web server)
EXPOSE 8000 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from app.config import get_config; get_config()" || exit 1

# Команда запуска (по умолчанию запускаем бота)
CMD ["python", "main.py"]