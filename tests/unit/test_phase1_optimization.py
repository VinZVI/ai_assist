import pytest

from app.utils.cache_keys import CacheKeyManager
from app.utils.security import SecurityValidator
from app.utils.validators import InputValidator


def test_input_validator() -> None:
    """Test the InputValidator class."""
    # Test sanitize_text
    # Note: html.escape converts single quotes to &#x27; in Python 3.12+
    sanitized = InputValidator.sanitize_text("<script>alert('xss')</script>")
    assert "&lt;script&gt;" in sanitized
    assert "&lt;/script&gt;" in sanitized
    assert "alert" in sanitized
    assert "<script>" not in sanitized

    assert InputValidator.sanitize_text("normal text") == "normal text"

    # Test validate_message_length
    valid, _msg = InputValidator.validate_message_length("short message")
    assert valid is True

    long_message = "a" * (InputValidator.MAX_MESSAGE_LENGTH + 1)
    valid, _msg = InputValidator.validate_message_length(long_message)
    assert valid is False

    # Test validate_user_data
    user_data = {
        "username": "test_user",
        "first_name": "John<script>",
        "last_name": "Doe",
    }
    validated = InputValidator.validate_user_data(user_data)
    assert "username" in validated
    assert "first_name" in validated
    assert "last_name" in validated
    assert "<script>" not in validated["first_name"]


def test_security_validator() -> None:
    """Test the SecurityValidator class."""
    # Test validate_production_token
    # Valid Telegram token format: 8-10 digits, colon, 35 alphanumeric characters with _ and -
    # Our test token: 9 digits + colon + 35 characters = 45 total
    valid, _msg = SecurityValidator.validate_production_token(
        "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi", "telegram"
    )
    assert valid is True

    # Test with invalid format
    valid, _msg = SecurityValidator.validate_production_token(
        "invalid_token", "telegram"
    )
    assert valid is False

    # Test with dangerous default
    valid, _msg = SecurityValidator.validate_production_token(
        "your_telegram_bot_token_here", "telegram"
    )
    assert valid is False

    # Valid API key (32+ characters)
    valid, _msg = SecurityValidator.validate_production_token(
        "sk-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", "api"
    )
    assert valid is True

    # Invalid API key (too short)
    valid, _msg = SecurityValidator.validate_production_token("short_key", "api")
    assert valid is False


def test_cache_key_manager() -> None:
    """Test the CacheKeyManager class."""
    # Test user_key
    user_key = CacheKeyManager.user_key(123456789)
    assert user_key == "user:v1:123456789"

    # Test conversation_context_key
    conv_key = CacheKeyManager.conversation_context_key(123456789, 6, 12)
    assert conv_key == "conv_ctx:v1:123456789:6:12"

    # Test conversation_backup_key
    backup_key = CacheKeyManager.conversation_backup_key(123456789)
    assert backup_key == "conv_backup:v1:123456789"

    # Test parse_key
    parsed = CacheKeyManager.parse_key("user:v1:123456789")
    assert parsed["valid"] is True
    assert parsed["prefix"] == "user"
    assert parsed["version"] == "v1"
    assert parsed["components"] == ["123456789"]
