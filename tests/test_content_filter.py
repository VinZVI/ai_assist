"""
Tests for ContentFilterMiddleware
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, Message

from app.middleware.content_filter import ContentFilterMiddleware


@pytest.fixture
def content_filter_middleware() -> ContentFilterMiddleware:
    """Create an instance of ContentFilterMiddleware for testing."""
    return ContentFilterMiddleware()


@pytest.mark.asyncio
async def test_content_filter_middleware_init() -> None:
    """Test initialization of ContentFilterMiddleware."""
    middleware = ContentFilterMiddleware()
    assert isinstance(middleware, ContentFilterMiddleware)


@pytest.mark.asyncio
async def test_filter_clean_message(
    content_filter_middleware: ContentFilterMiddleware,
) -> None:
    """Test filtering a clean message."""
    # Create a mock message with clean content
    message = MagicMock(spec=Message)
    message.text = "Hello! How are you doing today?"
    message.answer = AsyncMock()

    # Process the message
    result = await content_filter_middleware._filter_content(message)

    # Verify the result - should be allowed (True)
    assert result is True
    # Verify that no response was sent
    message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_filter_extremist_content(
    content_filter_middleware: ContentFilterMiddleware,
) -> None:
    """Test filtering extremist content."""
    # Create a mock message with extremist content
    message = MagicMock(spec=Message)
    message.text = "I support terrorism and violence against innocent people."
    message.answer = AsyncMock()

    # Process the message
    result = await content_filter_middleware._filter_content(message)

    # Verify the result - should be blocked (False)
    assert result is False
    # Verify that a response was sent
    message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_filter_illegal_content(
    content_filter_middleware: ContentFilterMiddleware,
) -> None:
    """Test filtering illegal content."""
    # Create a mock message with illegal content
    message = MagicMock(spec=Message)
    message.text = "I want to buy some narcotics."
    message.answer = AsyncMock()

    # Process the message
    result = await content_filter_middleware._filter_content(message)

    # Verify the result - should be blocked (False)
    assert result is False
    # Verify that a response was sent
    message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_filter_personal_data_warning(
    content_filter_middleware: ContentFilterMiddleware,
) -> None:
    """Test filtering content with personal data."""
    # Create a mock message with personal data
    message = MagicMock(spec=Message)
    message.text = "My email is test@example.com and my phone is 12345678901."
    message.answer = AsyncMock()

    # Process the message
    result = await content_filter_middleware._filter_content(message)

    # Verify the result - should be allowed (True) but with a warning
    assert result is True
    # Verify that a warning response was sent
    message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_process_callback_query_ignored(
    content_filter_middleware: ContentFilterMiddleware,
) -> None:
    """Test that callback queries are ignored."""
    # Create a mock callback query
    callback_query = MagicMock(spec=CallbackQuery)
    callback_query.data = "some_callback_data"
    callback_query.answer = AsyncMock()

    # Process the callback query
    result = await content_filter_middleware.process_callback_query(callback_query, {})

    # Verify the result
    assert result is True
    # Verify that no response was sent
    callback_query.answer.assert_not_called()


@pytest.mark.asyncio
async def test_get_stats(content_filter_middleware: ContentFilterMiddleware) -> None:
    """Test getting statistics."""
    # Get initial stats
    initial_stats = content_filter_middleware.get_stats()

    # Verify the structure
    assert "total_messages" in initial_stats
    assert "blocked_messages" in initial_stats
    assert "warning_messages" in initial_stats
    assert "allowed_messages" in initial_stats

    # All should be zero initially
    assert initial_stats["total_messages"] == 0
    assert initial_stats["blocked_messages"] == 0
    assert initial_stats["warning_messages"] == 0
    assert initial_stats["allowed_messages"] == 0


@pytest.mark.asyncio
async def test_reset_stats(content_filter_middleware: ContentFilterMiddleware) -> None:
    """Test resetting statistics."""
    # Manually increment some stats
    content_filter_middleware.stats["total_messages"] = 10
    content_filter_middleware.stats["blocked_messages"] = 3
    content_filter_middleware.stats["warning_messages"] = 2
    content_filter_middleware.stats["allowed_messages"] = 5

    # Reset stats
    content_filter_middleware.reset_stats()

    # Verify all stats are zero
    stats = content_filter_middleware.get_stats()
    assert stats["total_messages"] == 0
    assert stats["blocked_messages"] == 0
    assert stats["warning_messages"] == 0
    assert stats["allowed_messages"] == 0
