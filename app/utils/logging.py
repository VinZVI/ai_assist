"""
@file: utils/logging.py
@description: Настройка централизованного логирования приложения
@dependencies: loguru
@created: 2025-09-07
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loguru import logger


def json_formatter(record: dict[str, Any]) -> str:
    """
    Форматирование логов в JSON формат.

    Args:
        record: Запись лога от loguru

    Returns:
        Строка в JSON формате
    """
    # Создаем структурированную запись
    log_entry = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "logger": record["name"],
        "function": record["function"],
        "line": record["line"],
        "message": record["message"],
        "module": record["module"],
        "process": record["process"].id,
        "thread": record["thread"].id,
    }

    # Добавляем дополнительные данные если есть
    if record.get("extra"):
        log_entry["extra"] = record["extra"]

    # Добавляем информацию об исключении если есть
    if record["exception"]:
        log_entry["exception"] = {
            "type": record["exception"].type.__name__,
            "value": str(record["exception"].value),
            "traceback": record["exception"].traceback,
        }

    return json.dumps(log_entry, ensure_ascii=False)


def console_formatter(record: dict[str, Any]) -> str:
    """
    Форматирование логов для консоли с эмодзи и цветами.

    Args:
        record: Запись лога от loguru

    Returns:
        Отформатированная строка для консоли
    """
    # Эмодзи для разных уровней
    level_emoji = {
        "TRACE": "🔍",
        "DEBUG": "🐛",
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "💥",
    }

    emoji = level_emoji.get(record["level"].name, "📝")

    # Цветовое кодирование
    colors = {
        "TRACE": "<dim>",
        "DEBUG": "<blue>",
        "INFO": "<cyan>",
        "SUCCESS": "<green>",
        "WARNING": "<yellow>",
        "ERROR": "<red>",
        "CRITICAL": "<red><bold>",
    }

    color = colors.get(record["level"].name, "")

    # Формат для консоли
    time_str = record["time"].strftime("%H:%M:%S")
    level_str = record["level"].name.ljust(8)
    module_str = f"{record['module']}:{record['line']}"

    return (
        f"{color}{emoji} {time_str} | "
        f"{level_str} | "
        f"{module_str:<20} | "
        f"{record['message']}"
        f"</>"
    )


def setup_logging(
    log_level: str = "INFO",
    enable_json: bool = False,
    log_file_path: Path | None = None,
    enable_console: bool = True,
    enable_request_logging: bool = False,
) -> None:
    """
    Настройка системы логирования.

    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_json: Включить JSON формат для файлов
        log_file_path: Путь к файлу логов (если None - логи только в консоль)
        enable_console: Включить вывод в консоль
        enable_request_logging: Включить детальное логирование запросов
    """
    # Удаляем стандартный handler
    logger.remove()

    # Настройка консольного вывода
    if enable_console:
        logger.add(
            sys.stdout,
            format=console_formatter,
            level=log_level,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )

    # Настройка файлового вывода
    if log_file_path:
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        if enable_json:
            # JSON формат для структурированных логов
            logger.add(
                log_file_path / "app.json",
                format=json_formatter,
                level=log_level,
                rotation="10 MB",
                retention="30 days",
                compression="gz",
                backtrace=True,
                diagnose=True,
            )

        # Обычный текстовый формат для удобочитаемости
        logger.add(
            log_file_path / "app.log",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}"
            ),
            level=log_level,
            rotation="10 MB",
            retention="30 days",
            compression="gz",
            backtrace=True,
            diagnose=True,
        )

        # Отдельный файл для ошибок
        logger.add(
            log_file_path / "errors.log",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}\n"
                "{exception}"
            ),
            level="ERROR",
            rotation="10 MB",
            retention="60 days",
            compression="gz",
            backtrace=True,
            diagnose=True,
        )

    # Настройки для детального логирования запросов
    if enable_request_logging:
        # Отдельный логгер для HTTP запросов
        logger.add(
            log_file_path / "requests.log" if log_file_path else sys.stdout,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "REQUEST | "
                "{extra[method]} {extra[url]} | "
                "Status: {extra[status_code]} | "
                "Time: {extra[response_time]}ms"
            ),
            filter=lambda record: "request" in record.get("extra", {}),
            level="INFO",
        )

    logger.info("🚀 Система логирования инициализирована")
    logger.debug(f"📊 Уровень логирования: {log_level}")
    logger.debug(f"📁 JSON формат: {'включен' if enable_json else 'отключен'}")
    logger.debug(f"📋 Консольный вывод: {'включен' if enable_console else 'отключен'}")
    logger.debug(
        f"🌐 Логирование запросов: {'включено' if enable_request_logging else 'отключено'}"
    )


def get_logger(name: str) -> "logger":
    """
    Получение логгера для конкретного модуля.

    Args:
        name: Имя модуля/компонента

    Returns:
        Настроенный логгер
    """
    return logger.bind(component=name)


def log_function_call(func_name: str, **kwargs: Any) -> None:
    """
    Логирование вызова функции с параметрами.

    Args:
        func_name: Имя функции
        **kwargs: Параметры функции (будут замаскированы если содержат секреты)
    """
    # Маскируем чувствительные данные
    safe_kwargs = {}
    sensitive_keys = {"password", "token", "key", "secret", "api_key"}

    for key, value in kwargs.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            safe_kwargs[key] = "***MASKED***"
        else:
            safe_kwargs[key] = value

    logger.debug(f"🔧 Вызов функции {func_name}", extra={"parameters": safe_kwargs})


def log_performance(operation: str, duration_ms: float, **context: Any) -> None:
    """
    Логирование метрик производительности.

    Args:
        operation: Название операции
        duration_ms: Время выполнения в миллисекундах
        **context: Дополнительный контекст
    """
    logger.info(
        f"⏱️ {operation} выполнено за {duration_ms:.2f}ms",
        extra={
            "performance": {
                "operation": operation,
                "duration_ms": duration_ms,
                **context,
            },
        },
    )


def log_user_action(user_id: int, action: str, **details: Any) -> None:
    """
    Логирование действий пользователей.

    Args:
        user_id: ID пользователя
        action: Описание действия
        **details: Дополнительные детали
    """
    logger.info(
        f"👤 Пользователь {user_id}: {action}",
        extra={
            "user_action": {
                "user_id": user_id,
                "action": action,
                "timestamp": datetime.now(tz=UTC).isoformat(),
                **details,
            },
        },
    )


def log_api_request(
    method: str,
    url: str,
    status_code: int,
    response_time: float,
) -> None:
    """
    Логирование API запросов.

    Args:
        method: HTTP метод
        url: URL запроса
        status_code: Код ответа
        response_time: Время ответа в миллисекундах
    """
    logger.info(
        f"🌐 {method} {url} -> {status_code} ({response_time:.0f}ms)",
        extra={
            "request": True,
            "method": method,
            "url": url,
            "status_code": status_code,
            "response_time": response_time,
        },
    )


# Экспорт для удобного использования
__all__ = [
    "console_formatter",
    "get_logger",
    "json_formatter",
    "log_api_request",
    "log_function_call",
    "log_performance",
    "log_user_action",
    "setup_logging",
]
