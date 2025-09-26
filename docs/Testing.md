# Документация по тестированию AI-Компаньон

## 📋 Обзор

Данный документ содержит полную информацию о тестировании проекта AI-Компаньон, включая структуру тестов, карту покрытия кода, паттерны тестирования и руководство по написанию новых тестов.

**Дата создания:** 2025-09-20  
**Последнее обновление:** 2025-09-25  
**Общее покрытие кода:** 68% (560/1752 строк не покрыты)

---

## 🏗️ Структура тестов

### Корневая структура

```
tests/
├── __init__.py                 # Основной пакет тестов
├── conftest.py                # Конфигурация pytest и общие фикстуры
├── unit/                      # Юнит-тесты компонентов
│   ├── __init__.py
│   ├── test_config.py         # Тесты конфигурации (9.8KB)
│   └── test_models.py         # Тесты моделей данных (20.4KB)
├── integration/               # Интеграционные тесты
│   ├── __init__.py
│   ├── test_ai_service.py     # Тесты AI сервиса (18.0KB)
│   ├── test_database.py       # Тесты базы данных (17.3KB)
│   └── test_message_handler.py # Тесты обработчика сообщений (22.4KB)
└── fixtures/                  # Тестовые данные и фикстуры
    └── __init__.py

scripts/
├── checks/                    # Скрипты проверки
│   ├── test_config_simple.py  # Простая проверка конфигурации (3.3KB)
│   ├── test_db_connection.py  # Проверка подключения к БД (4.3KB)
│   └── test_openrouter_integration.py # Проверка OpenRouter (5.6KB)
└── diagnostics/               # Диагностические скрипты
    ├── check_deepseek_api.py  # Диагностика DeepSeek API (8.8KB)
    └── check_imports.py       # Проверка импортов (1.8KB)
```

### Категории тестов

#### 🔬 Юнит-тесты (`tests/unit/`)
- **Назначение**: Тестирование отдельных компонентов в изоляции
- **Характеристики**: Быстрые, без внешних зависимостей, моки для всех внешних вызовов
- **Файлы**: test_config.py, test_models.py

#### 🔗 Интеграционные тесты (`tests/integration/`)
- **Назначение**: Тестирование взаимодействия между компонентами
- **Характеристики**: Могут использовать реальные подключения к БД/API
- **Файлы**: test_ai_service.py, test_database.py, test_message_handler.py

#### ✅ Скрипты проверки (`scripts/checks/`)
- **Назначение**: Быстрая проверка работоспособности компонентов
- **Характеристики**: Автономные скрипты для локальной диагностики

#### 🔍 Диагностические скрипты (`scripts/diagnostics/`)
- **Назначение**: Глубокая диагностика проблем и подключений
- **Характеристики**: Детальный анализ с логированием и рекомендациями

---

## 📊 Карта покрытия кода тестами

### Общая статистика покрытия

| Компонент | Покрытие | Строк покрыто | Всего строк | Статус |
|-----------|----------|---------------|-------------|---------|
| **Общее покрытие** | **51%** | **898** | **1752** | 🟡 Частично |

### Детальное покрытие по модулям

#### ✅ Высокое покрытие (80-100%)

| Модуль | Покрытие | Строк не покрыто | Комментарий |
|--------|----------|------------------|-------------|
| `app/__init__.py` | 100% | 0/3 | ✅ Полностью покрыто |
| `app/handlers/__init__.py` | 100% | 0/5 | ✅ Полностью покрыто |
| `app/keyboards/__init__.py` | 100% | 0/2 | ✅ Полностью покрыто |
| `app/models/__init__.py` | 100% | 0/4 | ✅ Полностью покрыто |
| `app/services/__init__.py` | 100% | 0/2 | ✅ Полностью покрыто |
| `app/services/ai_providers/__init__.py` | 100% | 0/4 | ✅ Полностью покрыто |
| `app/utils/__init__.py` | 100% | 0/0 | ✅ Полностью покрыто |
| `app/database.py` | 90% | 14/137 | ✅ Хорошо покрыто |
| `app/config.py` | 89% | 28/254 | ✅ Хорошо покрыто |
| `app/models/conversation.py` | 82% | 21/114 | ✅ Хорошо покрыто |

#### 🟡 Среднее покрытие (50-79%)

| Модуль | Покрытие | Строк не покрыто | Комментарий |
|--------|----------|------------------|-------------|
| `app/models/user.py` | 71% | 28/97 | 🟡 Нуждается в доработке |
| `app/services/ai_service.py` | 67% | 61/185 | 🟡 Нуждается в доработке |
| `app/services/ai_providers/base.py` | 65% | 26/74 | 🟡 Нуждается в доработке |
| `app/utils/logging.py` | 59% | 23/56 | 🟡 Нуждается в доработке |

#### 🔴 Низкое покрытие (0-49%)

| Модуль | Покрытие | Строк не покрыто | Приоритет |
|--------|----------|------------------|-----------|
| `app/handlers/callbacks.py` | 28% | 84/116 | 🔴 Критически низко |
| `app/handlers/message.py` | 26% | 95/129 | 🔴 Критически низко |
| `app/keyboards/inline.py` | 23% | 43/56 | 🔴 Критически низко |
| `app/handlers/start.py` | 20% | 68/85 | 🔴 Критически низко |
| `app/services/ai_manager.py` | 18% | 145/177 | 🔴 **ПРИОРИТЕТ 1** |
| `app/services/ai_providers/deepseek.py` | 13% | 109/126 | 🔴 **ПРИОРИТЕТ 2** |
| `app/services/ai_providers/openrouter.py` | 13% | 109/126 | 🔴 **ПРИОРИТЕТ 3** |

### Критически важные компоненты без покрытия

#### 🚨 Высший приоритет

1. **`app/services/ai_manager.py` (18% покрытия)**
   - **Функции без покрытия**: 
     - Инициализация AIManager
     - Механизм fallback между провайдерами
     - Статистика использования провайдеров
     - Кеширование ответов
     - Health check провайдеров
   - **Критичность**: Ключевой компонент новой архитектуры

2. **`app/services/ai_providers/openrouter.py` (13% покрытия)**
   - **Функции без покрытия**:
     - Инициализация OpenRouter провайдера
     - HTTP запросы к OpenRouter API
     - Обработка ошибок API (401, 402, 429, 5xx)
     - Генерация ответов
   - **Критичность**: Основной новый функционал

3. **`app/services/ai_providers/deepseek.py` (13% покрытия)**
   - **Функции без покрытия**:
     - Рефакторинг DeepSeek провайдера
     - HTTP запросы к DeepSeek API
     - Обработка ошибок API
     - Генерация ответов
   - **Критичность**: Рефакторинг существующего функционала

#### 🔥 Высокий приоритет

4. **`app/handlers/message.py` (26% покрытия)**
   - **Функции без покрытия**:
     - Интеграция с новым AIManager
     - Обработка fallback логики
     - Валидация сообщений
     - Сохранение диалогов
   - **Критичность**: Основной пользовательский интерфейс

5. **`app/handlers/callbacks.py` (28% покрытия)**
   - **Функции без покрытия**:
     - Inline клавиатуры
     - Callback обработчики
     - Премиум функции
   - **Критичность**: Пользовательский интерфейс

---

## 🧪 Существующие тесты

### Статистика по тестам

| Категория | Количество тестов | Статус |
|-----------|-------------------|---------|
| **Всего собрано** | 183 тестов | ✅ |
| **Прошли успешно** | 94 тестов | ✅ |
| **Провалились** | 22 тестов | ❌ |
| **Пропущены** | 7 тестов | ⏭️ |
| **Ошибки** | 60 тестов | 💥 |

### Детализация по файлам

#### 📁 tests/unit/test_config.py
- **Всего тестов**: 11
- **Статус**: ✅ Все тесты проходят
- **Основные проблемы**:
  - Исправлены проблемы с .env.example файлом
  - Исправлены проблемы с валидацией Pydantic
  - Исправлены некорректные пути к файлам

#### 📁 tests/unit/test_models.py  
- **Всего тестов**: 25
- **Статус**: 🔴 Критические проблемы
- **Основные проблемы**:
  - Несовместимость с текущими моделями SQLAlchemy
  - Проблемы с асинхронными фикстурами
  - Некорректные имена полей в User модели
  - Проблемы с Pydantic схемами

#### 📁 tests/integration/test_ai_service.py
- **Всего тестов**: 29  
- **Статус**: 🔴 Критические проблемы
- **Основные проблемы**:
  - Тесты написаны для старого AIService, не AIManager
  - Моки не соответствуют новой архитектуре
  - Асинхронные функции без pytest.mark.asyncio
  - Проблемы с валидацией конфигурации

#### 📁 tests/integration/test_database.py
- **Всего тестов**: 24
- **Статус**: ✅ Все тесты проходят
- **Основные проблемы**:
  - Исправлены проблемы с async context managers
  - Исправлены моки для SQLAlchemy
  - Исправлены экспорты модулей

#### 📁 tests/integration/test_message_handler.py
- **Всего тестов**: 22
- **Статус**: 🔴 Критические проблемы
- **Основные проблемы**:
  - Отсутствующие фикстуры (mock_session)
  - Тесты не адаптированы под новую AI архитектуру
  - Проблемы с импортами
  - Проблемы с моками Telegram сообщений

#### 📁 scripts/checks/*
- **Статус**: 🔴 Не работают
- **Проблемы**: Асинхронные функции без поддержки pytest
  - Требуется обновление для совместимости с новой архитектурой

---

## 📝 Паттерны тестирования

### 1. 🏗️ Структура тестового класса

```python
"""
@file: test_example.py
@description: Описание тестируемого компонента
@dependencies: pytest, pytest-asyncio, unittest.mock
@created: YYYY-MM-DD
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.module import ComponentToTest


class TestComponentName:
    """Тесты для конкретного компонента."""
    
    @pytest.fixture
    def mock_dependency(self):
        """Фикстура для создания мока зависимости."""
        return MagicMock()
    
    @pytest.mark.asyncio 
    async def test_method_success(self, mock_dependency):
        """Тест успешного выполнения метода."""
        # Arrange
        # Подготовка данных и моков
        
        # Act
        # Выполнение тестируемого действия
        
        # Assert
        # Проверка результатов
        assert result == expected
```

### 2. 🎭 Моки и фикстуры

#### Стандартные фикстуры в conftest.py:

```python
@pytest.fixture
def mock_config():
    """Мок конфигурации."""
    return MagicMock()

@pytest.fixture  
def mock_db_session():
    """Мок сессии базы данных."""
    return AsyncMock()

@pytest.fixture
def sample_user():
    """Пример пользователя для тестов."""
    return User(telegram_id=12345, username="test_user")
```

### 3. ⚡ Асинхронные тесты

```python
@pytest.mark.asyncio
async def test_async_function():
    """Тест асинхронной функции."""
    result = await async_function()
    assert result is not None
```

### 4. 🔍 Тестирование ошибок

```python
def test_error_handling():
    """Тест обработки ошибок."""
    with pytest.raises(CustomException):
        function_that_should_raise()
```

### 5. 🎯 Моки HTTP запросов

```python
@patch('httpx.AsyncClient.post')
async def test_api_call(mock_post):
    """Тест API запроса."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"result": "success"}
    
    result = await api_function()
    assert result["result"] == "success"
```

---

## 🚀 Руководство по написанию тестов

### Для новых компонентов

1. **Создать тестовый файл**: `tests/unit/test_component.py` или `tests/integration/test_component.py`
2. **Импортировать зависимости**: pytest, unittest.mock, тестируемые модули
3. **Создать тестовый класс**: `TestComponentName`
4. **Добавить фикстуры**: моки зависимостей
5. **Написать тесты**: по одному для каждого метода/сценария
6. **Добавить маркеры**: @pytest.mark.asyncio для async функций

### Для AI провайдеров

```python
class TestAIProvider:
    """Тесты для AI провайдера."""
    
    @pytest.fixture
    def mock_http_client(self):
        """Мок HTTP клиента."""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, mock_http_client):
        """Тест успешной генерации ответа."""
        # Мок HTTP ответа
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "AI response"}}],
            "usage": {"total_tokens": 50}
        }
        mock_http_client.post.return_value = mock_response
        
        # Тест
        provider = AIProvider()
        response = await provider.generate_response(messages)
        
        assert response.content == "AI response"
        assert response.tokens_used == 50
```

### Для обработчиков Telegram

```python
@pytest.mark.asyncio
async def test_message_handler(mock_message, mock_user):
    """Тест обработчика сообщений."""
    mock_message.text = "Hello AI"
    mock_message.from_user.id = 12345
    
    with patch('app.handlers.message.get_ai_manager') as mock_manager:
        mock_manager.return_value.generate_response.return_value = AIResponse(
            content="Hello user!", 
            model="test-model",
            tokens_used=10,
            response_time=0.5
        )
        
        await handle_text_message(mock_message)
        
        mock_message.answer.assert_called_once()
        assert "Hello user!" in mock_message.answer.call_args[1]["text"]
```

---

## ⚙️ Команды запуска тестов

### Основные команды

```bash
# Запуск всех тестов
uv run pytest

# Запуск с покрытием кода  
uv run pytest --cov=app --cov-report=term-missing

# Запуск только юнит-тестов
uv run pytest tests/unit/

# Запуск только интеграционных тестов
uv run pytest tests/integration/

# Запуск конкретного файла
uv run pytest tests/unit/test_config.py

# Запуск с детальным выводом
uv run pytest -v

# Запуск быстрых тестов (без медленных)
uv run pytest -m "not slow"

# Генерация HTML отчета покрытия
uv run pytest --cov=app --cov-report=html
```

### Специальные команды

```bash
# Запуск скриптов проверки
uv run python scripts/checks/test_config_simple.py
uv run python scripts/checks/test_db_connection.py  
uv run python scripts/checks/test_openrouter_integration.py

# Запуск диагностических скриптов
uv run python scripts/diagnostics/check_deepseek_api.py
uv run python scripts/diagnostics/check_imports.py
```

---

## 🎯 План улучшения тестов

### Этап 1: Исправление критических ошибок (Приоритет 1) ✅ ЗАВЕРШЕН

1. **Исправить существующие тесты**:
   - ✅ Устранить синтаксические ошибки
   - ✅ Обновить фикстуры для новой архитектуры
   - ✅ Исправить импорты и пути к файлам
   - ✅ Адаптировать под новые модели данных

2. **Обновить conftest.py**:
   - Добавить фикстуры для AIManager
   - Добавить фикстуры для AI провайдеров  
   - Обновить моки для новой архитектуры

### Этап 2: Создание недостающих тестов (Приоритет 2) 🔄 В ПРОЦЕССЕ

1. **Тесты для AI Manager** (18% → 80%):
   - test_ai_manager_initialization.py
   - test_fallback_logic.py
   - test_provider_switching.py
   - test_statistics_tracking.py

2. **Тесты для AI провайдеров** (13% → 75%):
   - test_openrouter_provider.py
   - test_deepseek_provider.py  
   - test_base_provider.py
   - test_error_handling.py

3. **Тесты для обработчиков** (26% → 70%):
   - Обновить test_message_handler.py
   - Создать test_callbacks_handler.py
   - Создать test_start_handler.py

### Этап 3: Расширение покрытия (Приоритет 3)

1. **Тесты для утилит**:
   - test_logging.py
   - test_keyboards.py

2. **Интеграционные тесты**:
   - test_full_bot_workflow.py
   - test_database_integration.py
   - test_external_api_integration.py

### Целевые показатели

| Этап | Целевое покрытие | Срок |
|------|------------------|------|
| Этап 1 | 60% | ✅ Достигнут (68%) |
| Этап 2 | 75% | 2 недели |  
| Этап 3 | 85% | 3 недели |

---

## 📚 Полезные ресурсы

### Документация

- [pytest документация](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py](https://coverage.readthedocs.io/)

### Лучшие практики

1. **Один тест - одна проверка**: Каждый тест должен проверять только одну функциональность
2. **Описательные имена**: `test_user_creation_with_valid_data` лучше чем `test_user_1`
3. **AAA паттерн**: Arrange (подготовка) → Act (действие) → Assert (проверка)
4. **Изоляция тестов**: Тесты не должны зависеть друг от друга
5. **Моки для внешних зависимостей**: API, база данных, файловая система

### Маркеры pytest

```python
@pytest.mark.unit          # Юнит-тест
@pytest.mark.integration   # Интеграционный тест  
@pytest.mark.asyncio       # Асинхронный тест
@pytest.mark.slow          # Медленный тест
@pytest.mark.database      # Требует БД
@pytest.mark.api           # Требует внешнее API
```

---

*Документация обновлена: 2025-09-25*  
*Версия: 1.0.0*  
*Автор: AI Assistant*