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
    result = content_filter_middleware._filter_content(message.text)

    # Verify the result - should be allowed
    assert result["action"] == "allow"
    # Verify that no response was sent
    message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_filter_extremist_content(
    content_filter_middleware: ContentFilterMiddleware,
) -> None:
    """Test filtering extremist content."""
    # Test the _filter_content method directly
    text = "I support terrorism and violence against innocent people."

    # Process the message
    result = content_filter_middleware._filter_content(text)

    # Verify the result - should be blocked
    assert result["action"] == "block"


@pytest.mark.asyncio
async def test_filter_illegal_content(
    content_filter_middleware: ContentFilterMiddleware,
) -> None:
    """Test filtering illegal content."""
    # Test the _filter_content method directly
    text = "I want to buy some narcotics."

    # Process the message
    result = content_filter_middleware._filter_content(text)

    # Verify the result - should be blocked
    assert result["action"] == "block"


@pytest.mark.asyncio
async def test_filter_personal_data_warning(
    content_filter_middleware: ContentFilterMiddleware,
) -> None:
    """Test filtering content with personal data."""
    # Test the _filter_content method directly
    text = "My email is test@example.com and my phone is 12345678901."

    # Process the message
    result = content_filter_middleware._filter_content(text)

    # Verify the result - should have a warning
    assert result["action"] == "warn"


@pytest.mark.asyncio
async def test_process_callback_query_ignored(
    content_filter_middleware: ContentFilterMiddleware,
) -> None:
    """Test that callback queries are ignored."""
    # Create a mock callback query
    callback_query = MagicMock(spec=CallbackQuery)
    callback_query.data = "some_callback_data"
    callback_query.answer = AsyncMock()

    # Create a mock handler
    mock_handler = AsyncMock()

    # Process the callback query using the middleware
    await content_filter_middleware(mock_handler, callback_query, {})

    # Verify the result
    mock_handler.assert_called_once_with(callback_query, {})
    # Verify that no response was sent
    callback_query.answer.assert_not_called()


@pytest.mark.asyncio
async def test_get_stats() -> None:
    """Test getting statistics."""
    # Create a new instance to test with fresh stats
    content_filter = ContentFilterMiddleware()

    # Get initial stats
    initial_stats = content_filter.get_content_filter_stats()

    # Verify the structure
    assert "messages_filtered" in initial_stats
    assert "users_warned" in initial_stats
    assert "messages_blocked" in initial_stats

    # All should be zero initially
    assert initial_stats["messages_filtered"] == 0
    assert initial_stats["users_warned"] == 0
    assert initial_stats["messages_blocked"] == 0


@pytest.mark.asyncio
async def test_reset_stats() -> None:
    """Test resetting statistics."""
    # Create a new instance to test with
    content_filter = ContentFilterMiddleware()

    # Manually increment some stats using the class variable directly
    ContentFilterMiddleware._content_filter_stats["messages_filtered"] = 10
    ContentFilterMiddleware._content_filter_stats["users_warned"] = 3
    ContentFilterMiddleware._content_filter_stats["messages_blocked"] = 5

    # Reset stats
    content_filter.reset_content_filter_stats()

    # Verify all stats are zero
    stats = content_filter.get_content_filter_stats()
    assert stats["messages_filtered"] == 0
    assert stats["users_warned"] == 0
    assert stats["messages_blocked"] == 0
