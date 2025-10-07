# Документация по тестированию AI-Компаньон

## 📋 Обзор

Данный документ содержит полную информацию о тестировании проекта AI-Компаньон, включая структуру тестов, карту покрытия кода, паттерны тестирования и руководство по написанию новых тестов.

**Дата создания:** 2025-09-20  
**Последнее обновление:** 2025-10-07  
**Общее покрытие кода:** 68% (560/1752 строк не покрыты)

---

## 🏗️ Структура тестов

### Корневая структура

```
tests/
├── __init__.py                 # Основной пакет тестов
├── conftest.py                # Конфигурация pytest и общие фикстуры
├── fixtures/                  # Тестовые данные и фикстуры
│   └── __init__.py
├── unit/                      # Юнит-тесты компонентов
│   ├── __init__.py
│   ├── test_callbacks.py       # Тесты обработчиков callback-запросов
│   ├── test_config.py         # Тесты конфигурации (9.8KB)
│   ├── test_handlers.py       # Тесты обработчиков (новый файл)
│   └── test_models.py         # Тесты моделей данных (20.4KB)
├── integration/               # Интеграционные тесты
│   ├── __init__.py
│   ├── test_ai_manager.py     # Тесты AI менеджера (новый файл)
│   ├── test_ai_service.py     # Тесты AI сервиса (18.0KB)
│   ├── test_database.py       # Тесты базы данных (17.3KB)
│   ├── test_message_handler.py # Тесты обработчика сообщений (22.4KB)
│   └── test_user_service.py    # Тесты сервиса пользователей (новый файл)
└── conftest.py                # Конфигурация pytest

scripts/
├── __init__.py
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
- **Файлы**: test_callbacks.py, test_config.py, test_handlers.py, test_models.py

#### 🔗 Интеграционные тесты (`tests/integration/`)
- **Назначение**: Тестирование взаимодействия между компонентами
- **Характеристики**: Могут использовать реальные подключения к БД/API
- **Файлы**: test_ai_manager.py, test_ai_service.py, test_database.py, test_message_handler.py, test_user_service.py

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
| **Общее покрытие** | **78%** | **1367** | **1752** | 🟡 Частично |

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
| `app/database.py` | 95% | 7/137 | ✅ Хорошее покрытие |
| `app/config.py` | 89% | 28/254 | ✅ Хорошее покрытие |
| `app/models/conversation.py` | 82% | 21/114 | ✅ Хорошее покрытие |
| `app/models/user.py` | 85% | 15/97 | ✅ Хорошее покрытие |

#### 🟡 Среднее покрытие (50-79%)

| Модуль | Покрытие | Строк не покрыто | Комментарий |
|--------|----------|------------------|-------------|
| `app/services/ai_service.py` | 67% | 61/185 | 🟡 Нуждается в доработке |
| `app/services/ai_providers/base.py` | 65% | 26/74 | 🟡 Нуждается в доработке |
| `app/utils/logging.py` | 59% | 23/56 | 🟡 Нуждается в доработке |
| `app/log_lexicon/__init__.py` | 100% | 0/4 | ✅ Полностью покрыто |
| `app/log_lexicon/en.py` | 100% | 0/130 | ✅ Полностью покрыто |
| `app/log_lexicon/ru.py` | 100% | 0/130 | ✅ Полностью покрыто |

#### 🔴 Низкое покрытие (0-49%)

| Модуль | Покрытие | Строк не покрыто | Приоритет |
|--------|----------|------------------|-----------|
| `app/handlers/callbacks.py` | 28% | 84/116 | 🔴 Критически низко |
| `app/handlers/message.py` | 45% | 71/129 | 🟡 Улучшенное покрытие |
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
| **Всего собрано** | 185 тестов | ✅ |
| **Прошли успешно** | 132 тестов | ✅ |
| **Провалились** | 33 тестов | ❌ |
| **Пропущены** | 10 тестов | ⏭️ |
| **Ошибки** | 7 тестов | 💥 |

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
- **Статус**: 🟡 Улучшенное покрытие
- **Основные проблемы**:
  - Исправлена несовместимость с текущими моделями SQLAlchemy
  - Исправлены проблемы с асинхронными фикстурами
  - Исправлены некорректные имена полей в User модели
  - Исправлены проблемы с Pydantic схемами

#### 📁 tests/integration/test_ai_manager.py
- **Всего тестов**: 28
- **Статус**: 🟡 Улучшенное покрытие
- **Основные проблемы**:
  - Исправлены проблемы с моками для провайдеров
  - Исправлены ошибки в тестах fallback логики
  - Исправлены проблемы с асинхронными функциями

#### 📁 tests/integration/test_ai_service.py
- **Всего тестов**: 29  
- **Статус**: 🟡 Улучшенное покрытие
- **Основные проблемы**:
  - Исправлены проблемы с моками для AI провайдеров
  - Исправлены ошибки в тестах генерации ответов
  - Исправлены проблемы с асинхронными функциями

#### 📁 tests/integration/test_database.py
- **Всего тестов**: 32
- **Статус**: ✅ Все тесты проходят
- **Основные проблемы**:
  - Исправлены проблемы с асинхронными контекстными менеджерами
  - Исправлены ошибки в тестах создания таблиц
  - Исправлены проблемы с фикстурами

#### 📁 tests/integration/test_message_handler.py
- **Всего тестов**: 35
- **Статус**: ✅ Все тесты проходят
- **Основные проблемы**:
  - Исправлены проблемы с моками для сессий базы данных
  - Исправлены ошибки в тестах генерации AI ответов
  - Исправлены проблемы с асинхронными функциями

#### 📁 tests/unit/test_callbacks.py
- **Всего тестов**: 15
- **Статус**: ✅ Все тесты проходят
- **Основные проблемы**:
  - Исправлены проблемы с моками для callback-запросов
  - Исправлены ошибки в тестах inline клавиатур

#### 📁 tests/unit/test_handlers.py
- **Всего тестов**: 10
- **Статус**: ✅ Все тесты проходят
- **Основные проблемы**:
  - Созданы новые тесты для обработчиков команд
  - Исправлены проблемы с моками для Telegram API

---

## 🧩 Паттерны тестирования

### 🎯 Общие принципы

1. **Изоляция тестов**: Каждый тест должен быть независимым и не влиять на другие тесты
2. **Предсказуемость**: Тесты должны давать одинаковый результат при каждом запуске
3. **Скорость**: Тесты должны выполняться быстро (менее 1 секунды на тест)
4. **Читаемость**: Тесты должны быть легко читаемыми и понятными

### 🧱 Структура тестов

#### AAA паттерн (Arrange, Act, Assert)

```python
def test_example():
    # Arrange (Подготовка)
    mock_data = create_mock_data()
    service = MyService()
    
    # Act (Действие)
    result = service.process_data(mock_data)
    
    # Assert (Проверка)
    assert result == expected_result
```

#### Фикстуры и моки

```python
@pytest.fixture
def mock_user():
    """Фикстура для создания мок-пользователя."""
    return User(
        id=1,
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User"
    )

@patch("app.services.ai_manager.get_ai_manager")
def test_generate_ai_response_success(mock_get_ai_manager, mock_user):
    """Тест успешной генерации ответа от AI."""
    # Arrange
    mock_manager = Mock()
    mock_get_ai_manager.return_value = mock_manager
    mock_manager.generate_response.return_value = Mock(
        content="Test response",
        tokens_used=10,
        model="test-model",
        response_time=0.5
    )
    
    # Act
    result = generate_ai_response(mock_user, "Hello")
    
    # Assert
    assert len(result) == 4
    assert result[0] == "Test response"
    assert result[1] == 10
```

### 🧪 Типы тестов

#### 🧪 Юнит-тесты

Тестируют отдельные функции и методы в изоляции:

```python
def test_user_can_send_message():
    """Тест проверки возможности отправки сообщения пользователем."""
    user = User(daily_message_count=5, is_premium=False)
    assert user.can_send_message() == True
    
    user.daily_message_count = 100
    assert user.can_send_message() == False
```

#### 🔗 Интеграционные тесты

Тестируют взаимодействие между компонентами:

```python
@pytest.mark.asyncio
async def test_save_conversation_success():
    """Тест успешного сохранения диалога."""
    # Arrange
    mock_session = AsyncMock()
    user_id = 1
    user_message = "Hello"
    ai_response = "Hi there!"
    
    # Act
    result = await save_conversation(
        session=mock_session,
        user_id=user_id,
        user_message=user_message,
        ai_response=ai_response,
        ai_model="test-model",
        tokens_used=10,
        response_time=0.5
    )
    
    # Assert
    assert result == True
    assert mock_session.add.call_count == 2
    mock_session.commit.assert_called_once()
```

#### 🧪 Функциональные тесты

Тестируют полный функционал системы:

```python
@pytest.mark.asyncio
async def test_full_message_flow():
    """Тест полного цикла обработки сообщения."""
    # Arrange
    mock_message = create_mock_telegram_message("Hello, AI!")
    
    with patch("app.handlers.message.get_or_update_user") as mock_get_user:
        mock_get_user.return_value = create_mock_user()
        
        with patch("app.handlers.message.generate_ai_response") as mock_generate:
            mock_generate.return_value = ("AI response", 10, "test-model", 0.5)
            
            with patch("app.handlers.message.save_conversation") as mock_save:
                mock_save.return_value = True
                
                # Act
                await handle_text_message(mock_message)
                
                # Assert
                mock_get_user.assert_called_once_with(mock_message)
                mock_generate.assert_called_once()
                mock_save.assert_called_once()
                mock_message.answer.assert_called_once()
```

---

## 🛠️ Руководство по написанию тестов

### 📦 Создание новых тестов

1. **Определите тип теста**: Юнит, интеграционный или функциональный
2. **Создайте файл теста**: Используйте префикс `test_` и разместите в соответствующей директории
3. **Используйте правильные импорты**: Импортируйте только необходимые модули
4. **Следуйте AAA паттерну**: Arrange, Act, Assert
5. **Используйте фикстуры**: Для повторно используемых данных
6. **Мокайте внешние зависимости**: Используйте `unittest.mock` или `pytest-mock`
7. **Пишите понятные названия**: Используйте описательные имена функций
8. **Добавляйте документацию**: Пишите docstrings для тестов

### 🧪 Пример создания теста

```
# tests/unit/test_example.py

import pytest
from unittest.mock import AsyncMock, patch

from app.services.example_service import process_data
from app.models.user import User

class TestExampleService:
    """Тесты для примерного сервиса."""
    
    @pytest.fixture
    def mock_user(self) -> User:
        """Фикстура для создания мок-пользователя."""
        return User(
            id=1,
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User"
        )
    
    @pytest.mark.asyncio
    async def test_process_data_success(self, mock_user):
        """Тест успешной обработки данных."""
        # Arrange
        input_data = "test data"
        expected_result = "processed data"
        
        with patch("app.services.example_service.external_api_call") as mock_api:
            mock_api.return_value = expected_result
            
            # Act
            result = await process_data(mock_user, input_data)
            
            # Assert
            assert result == expected_result
            mock_api.assert_called_once_with(input_data)
```

### 🧪 Запуск тестов

```bash
# Запуск всех тестов
uv run pytest

# Запуск тестов с подробным выводом
uv run pytest -v

# Запуск тестов с покрытием кода
uv run pytest --cov=app

# Запуск тестов с покрытием и отчетом в HTML
uv run pytest --cov=app --cov-report=html

# Запуск конкретного файла тестов
uv run pytest tests/unit/test_config.py

# Запуск конкретного теста
uv run pytest tests/unit/test_config.py::test_load_config_success
```

---

## 📈 Метрики и статистика

### 📊 Текущее состояние тестов

- **Общее покрытие кода**: 68%
- **Всего тестов**: 185
- **Прошли успешно**: 132 (71%)
- **Провалились**: 33 (18%)
- **Пропущены**: 10 (5%)
- **Ошибки**: 7 (4%)

### 📈 Цели по улучшению

1. **Увеличить общее покрытие до 85%**
2. **Снизить количество проваленных тестов до 5%**
3. **Устранить все ошибки в тестах**
4. **Добавить тесты для критически важных компонентов**

### 📊 План улучшения

#### 🚨 Приоритет 1: Критические компоненты
- [ ] Добавить тесты для `app/services/ai_manager.py`
- [ ] Добавить тесты для `app/services/ai_providers/openrouter.py`
- [ ] Добавить тесты для `app/services/ai_providers/deepseek.py`

#### 🔥 Приоритет 2: Пользовательские интерфейсы
- [ ] Добавить тесты для `app/handlers/message.py`
- [ ] Добавить тесты для `app/handlers/callbacks.py`
- [ ] Добавить тесты для `app/handlers/start.py`

#### 📈 Приоритет 3: Улучшение покрытия
- [ ] Добавить тесты для `app/keyboards/inline.py`
- [ ] Добавить тесты для `app/services/ai_service.py`
- [ ] Добавить тесты для `app/services/ai_providers/base.py`

---

## 📚 Ресурсы

### 📖 Документация
- [Pytest Documentation](https://docs.pytest.org/)
- [Python Mock Library](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

### 🛠️ Инструменты
- **pytest**: Фреймворк для тестирования
- **pytest-asyncio**: Поддержка асинхронных тестов
- **pytest-cov**: Измерение покрытия кода
- **unittest.mock**: Библиотека для создания моков

### 📊 Команды

```bash
# Запуск всех тестов
uv run pytest

# Запуск с покрытием
uv run pytest --cov=app --cov-report=term-missing

# Запуск с подробным выводом
uv run pytest -v

# Запуск с отчетом в HTML
uv run pytest --cov=app --cov-report=html

# Запуск конкретного теста
uv run pytest tests/unit/test_config.py::test_load_config_success
```

---

*Последнее обновление: 2025-10-07 - Обновлена статистика тестов и добавлена информация о завершении рефакторинга лог-лексиконов*