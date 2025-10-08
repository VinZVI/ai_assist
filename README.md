# 🤖 AI-Компаньон

> Telegram-бот для эмоциональной поддержки с интеграцией OpenRouter API

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.22+-green.svg)](https://aiogram.dev)
[![uv](https://img.shields.io/badge/uv-latest-orange.svg)](https://docs.astral.sh/uv/)

## 📋 Описание

AI-Компаньон - это Telegram-бот, предназначенный для предоставления эмоциональной поддержки и психологического комфорта пользователям. Бот использует искусственный интеллект от OpenRouter для генерации персонализированных ответов и поддержания естественного диалога.

### ✨ Основные функции

- Эмоциональная поддержка и психологический комфорт
- Интеллектуальные диалоги с контекстом предыдущих сообщений
- Поддержка нескольких языков (RU/EN)
- Система лимитов сообщений для бесплатных пользователей
- Премиум-подписка через Telegram Stars
- Административная панель управления
- Множественные модели AI с автоматическим fallback

### 🎯 Целевая аудитория

Люди, нуждающиеся в эмоциональной поддержке, психологическом комфорте и дружеском общении.

## 🚀 Быстрый старт

### Требования

- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Telegram Bot Token
- OpenRouter API Key

### Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/yourusername/ai-assist.git
   cd ai-assist
   ```

2. Установите зависимости:
   ```bash
   uv sync
   ```

3. Создайте .env файл из примера:
   ```bash
   cp .env.example .env
   ```

4. Заполните .env файл реальными значениями

5. Запустите приложение:
   ```bash
   python main.py
   ```

## 📁 Структура проекта

```
ai_assist/
├── app/                    # Основное приложение
│   ├── handlers/          # Обработчики команд и сообщений
│   ├── models/            # Модели данных (SQLAlchemy)
│   ├── services/          # Бизнес-логика
│   ├── utils/             # Утилиты и вспомогательные функции
│   ├── keyboards/         # Inline клавиатуры
│   ├── constants/         # Константы и сообщения об ошибках
│   ├── lexicon/           # Лексиконы (модульная структура)
│   └── log_lexicon/       # Лог-лексиконы (модульная структура)
├── tests/                 # Тесты
├── docs/                  # Документация
├── scripts/               # Скрипты диагностики
├── alembic/               # Миграции базы данных
└── main.py               # Точка входа
```

## 🧪 Тестирование

Запуск всех тестов:
```bash
uv run pytest
```

Запуск тестов с покрытием:
```bash
uv run pytest --cov=app
```

## 📊 Мониторинг

Проверка состояния API:
```bash
python scripts/diagnostics/check_api_connectivity.py
```

## 🛠️ Разработка

### Code Style

Проект использует ruff для форматирования и линтинга кода:
```bash
ruff format .
ruff check --fix .
```

### Pre-commit хуки

Установите pre-commit хуки для автоматической проверки кода:
```bash
pre-commit install
```

## 📚 Документация

- [Project.md](docs/Project.md) - Полное описание проекта
- [Tasktracker.md](docs/Tasktracker.md) - Отслеживание задач
- [Diary.md](docs/Diary.md) - Дневник разработки
- [Testing.md](docs/Testing.md) - Документация по тестированию
- [Deployment.md](docs/Deployment.md) - Документация по деплою
- [Docker.md](docs/Docker.md) - Документация по Docker
- [qa.md](docs/qa.md) - Вопросы и ответы
- [changelog.md](docs/changelog.md) - Журнал изменений

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для вашей функции (`git checkout -b feature/AmazingFeature`)
3. Зафиксируйте изменения (`git commit -m 'Add some AmazingFeature'`)
4. Запушьте ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован по лицензии MIT - см. файл [LICENSE](LICENSE) для подробностей.

## 📞 Контакты

Если у вас есть вопросы, создайте issue в этом репозитории.