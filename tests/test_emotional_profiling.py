"""
Tests for EmotionalProfilingMiddleware
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, Message

from app.middleware.emotional_profiling import EmotionalProfilingMiddleware
from app.models.user import User


@pytest.fixture
def emotional_middleware() -> EmotionalProfilingMiddleware:
    """Create an instance of EmotionalProfilingMiddleware for testing."""
    return EmotionalProfilingMiddleware()


@pytest.fixture
def mock_user() -> User:
    """Create a mock user for testing."""
    user = MagicMock(spec=User)
    user.id = 12345
    user.emotional_traits = {}
    user.update_emotional_profile = AsyncMock()
    return user


@pytest.mark.asyncio
async def test_emotional_profiling_middleware_init() -> None:
    """Test initialization of EmotionalProfilingMiddleware."""
    middleware = EmotionalProfilingMiddleware()
    assert isinstance(middleware, EmotionalProfilingMiddleware)


@pytest.mark.asyncio
async def test_process_message_with_emotional_content(
    emotional_middleware: EmotionalProfilingMiddleware, mock_user: User
) -> None:
    """Test processing a message with emotional content."""
    # Create a mock message with emotional content
    message = MagicMock(spec=Message)
    message.text = (
        "I'm feeling really sad and depressed today. Nothing seems to go right."
    )
    message.from_user = MagicMock()
    message.from_user.id = 12345

    # Create mock data dictionary
    data = {"user": mock_user}

    # Process the message
    result = await emotional_middleware.process_message(message, data)

    # Verify the result
    assert result is True
    # Verify that update_emotional_profile was called
    mock_user.update_emotional_profile.assert_called_once()


@pytest.mark.asyncio
async def test_process_callback_query_ignored(
    emotional_middleware: EmotionalProfilingMiddleware, mock_user: User
) -> None:
    """Test that callback queries are ignored."""
    # Create a mock callback query
    callback_query = MagicMock(spec=CallbackQuery)
    callback_query.data = "some_callback_data"

    # Create mock data dictionary
    data = {"user": mock_user}

    # Process the callback query
    result = await emotional_middleware.process_callback_query(callback_query, data)

    # Verify the result
    assert result is True
    # Verify that update_emotional_profile was NOT called
    mock_user.update_emotional_profile.assert_not_called()


@pytest.mark.asyncio
async def test_extract_emotional_indicators_positive_content() -> None:
    """Test extracting emotional indicators from positive content."""
    middleware = EmotionalProfilingMiddleware()
    text = "I'm feeling great today! Everything is going well in my life. I'm so happy and excited!"

    indicators = middleware._extract_emotional_indicators(text)

    # Verify that we got some indicators
    assert isinstance(indicators, dict)
    assert "emotional_tone" in indicators
    assert "topics" in indicators


@pytest.mark.asyncio
async def test_extract_emotional_indicators_negative_content() -> None:
    """Test extracting emotional indicators from negative content."""
    middleware = EmotionalProfilingMiddleware()
    text = "I'm feeling really sad and depressed today. Nothing seems to go right. I'm so frustrated!"

    indicators = middleware._extract_emotional_indicators(text)

    # Verify that we got some indicators
    assert isinstance(indicators, dict)
    assert "emotional_tone" in indicators
    assert "topics" in indicators


@pytest.mark.asyncio
async def test_extract_emotional_indicators_neutral_content() -> None:
    """Test extracting emotional indicators from neutral content."""
    middleware = EmotionalProfilingMiddleware()
    text = "The weather is nice today. I'm going for a walk. It's a beautiful day."

    indicators = middleware._extract_emotional_indicators(text)

    # Verify that we got some indicators
    assert isinstance(indicators, dict)
    assert "emotional_tone" in indicators
    assert "topics" in indicators


@pytest.mark.asyncio
async def test_analyze_user_emotions_exception_handling(
    emotional_middleware: EmotionalProfilingMiddleware, mock_user: User
) -> None:
    """Test emotional analysis with exception handling."""
    # Create a mock message
    message = MagicMock(spec=Message)
    message.text = "Test message"
    message.from_user = MagicMock()
    message.from_user.id = 12345

    # Create mock data dictionary
    data = {"user": mock_user}

    # Mock the _extract_emotional_indicators method to raise an exception
    emotional_middleware._extract_emotional_indicators = MagicMock(
        side_effect=Exception("Test exception")
    )

    # Process the message - should not raise an exception
    result = await emotional_middleware.process_message(message, data)

    # Verify the result
    assert result is True
