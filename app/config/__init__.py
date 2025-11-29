"""
@file: config/__init__.py
@description: Configuration package initialization
@dependencies: app.config
@created: 2025-11-22
"""

import importlib.util
import os

# Get the directory of the current file (app/config/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (app/)
parent_dir = os.path.dirname(current_dir)
# Path to the config.py file
config_py_path = os.path.join(parent_dir, "config.py")

# Load the config.py module directly
spec = importlib.util.spec_from_file_location("config", config_py_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)

# Re-export all the important classes and functions
AppConfig = config_module.AppConfig
ConfigManager = config_module.ConfigManager
DatabaseConfig = config_module.DatabaseConfig
TelegramConfig = config_module.TelegramConfig
OpenRouterConfig = config_module.OpenRouterConfig
AIProviderConfig = config_module.AIProviderConfig
UserLimitsConfig = config_module.UserLimitsConfig
CacheConfig = config_module.CacheConfig
ConversationConfig = config_module.ConversationConfig
AdminConfig = config_module.AdminConfig
PaymentConfig = config_module.PaymentConfig
MonitoringConfig = config_module.MonitoringConfig
get_config = config_module.get_config
_config_manager = config_module._config_manager

__all__ = [
    "AppConfig",
    "ConfigManager",
    "DatabaseConfig",
    "TelegramConfig",
    "OpenRouterConfig",
    "AIProviderConfig",
    "UserLimitsConfig",
    "CacheConfig",
    "ConversationConfig",
    "AdminConfig",
    "PaymentConfig",
    "MonitoringConfig",
    "get_config",
    "_config_manager",
]