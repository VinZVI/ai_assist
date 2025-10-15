"""
Integration tests for emotional support features
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Message

from app.handlers.message import handle_text_message
from app.lexicon.gettext import get_text
from app.middleware.content_filter import ContentFilterMiddleware
from app.middleware.emotional_profiling import EmotionalProfilingMiddleware
from app.models.user import User as UserModel


@pytest.mark.asyncio
async def test_message_processing_with_emotional_content() -> None:
    """Test complete message processing with emotional content."""
    # Create a mock message with emotional content
    message = MagicMock(spec=Message)
    message.text = (
        "I'm feeling really sad and depressed today. Nothing seems to go right."
    )
    message.from_user = MagicMock()
    message.from_user.id = 12345
    message.from_user.username = "testuser"
    message.from_user.first_name = "Test"
    message.from_user.last_name = "User"
    message.from_user.language_code = "en"
    message.chat = MagicMock()
    message.chat.id = 12345
    message.answer = AsyncMock()
    message.bot = MagicMock()
    message.bot.send_chat_action = AsyncMock()

    # Create a mock user
    user = MagicMock(spec=UserModel)
    user.id = 12345
    user.can_send_message.return_value = True
    user.increment_message_count = AsyncMock()
    user.update_emotional_profile = AsyncMock()

    # Test successful execution with user and user_lang parameters
    with patch("app.handlers.message.generate_ai_response") as mock_generate_response:
        mock_generate_response.return_value = (
            "I understand you're feeling sad. It's okay to feel this way sometimes.",
            15,
            "test-model",
            0.1,
        )

        # Mock session context manager properly
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        with patch("app.handlers.message.get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Mock the get_recent_conversation_history function
            with patch(
                "app.services.conversation_service.get_recent_conversation_history"
            ) as mock_get_history:
                mock_get_history.return_value = []

                # Test successful execution
                await handle_text_message(message, user, "en")

                # Verify that the message was processed without errors
                message.answer.assert_called_with(
                    "I understand you're feeling sad. It's okay to feel this way sometimes."
                )


@pytest.mark.asyncio
async def test_content_filtering_integration() -> None:
    """Test integration of content filtering with message handling."""
    # Create content filter middleware
    content_filter = ContentFilterMiddleware()

    # Test filtering of clean content
    clean_message = MagicMock(spec=Message)
    clean_message.text = "Hello! How are you doing today?"
    clean_message.answer = AsyncMock()

    result = await content_filter._filter_content(clean_message)
    assert result is True
    clean_message.answer.assert_not_called()

    # Test filtering of extremist content
    extremist_message = MagicMock(spec=Message)
    extremist_message.text = "I support terrorism and violence against innocent people."
    extremist_message.answer = AsyncMock()

    result = await content_filter._filter_content(extremist_message)
    assert result is False
    extremist_message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_emotional_profiling_integration() -> None:
    """Test integration of emotional profiling with message handling."""
    # Create emotional profiling middleware
    emotional_profiling = EmotionalProfilingMiddleware()

    # Create a mock user
    user = MagicMock(spec=UserModel)
    user.id = 12345
    user.emotional_traits = {}
    user.update_emotional_profile = AsyncMock()

    # Test processing a message with emotional content
    message = MagicMock(spec=Message)
    message.text = (
        "I'm feeling really sad and depressed today. Nothing seems to go right."
    )
    message.from_user = MagicMock()
    message.from_user.id = 12345

    # Create mock data dictionary
    data = {"user": user}

    # Process the message
    result = await emotional_profiling.process_message(message, data)

    # Verify the result
    assert result is True
    # Verify that update_emotional_profile was called
    user.update_emotional_profile.assert_called_once()


@pytest.mark.asyncio
async def test_crisis_situation_handling() -> None:
    """Test handling of crisis situations."""
    # Create a mock message with crisis content
    message = MagicMock(spec=Message)
    message.text = "I don't want to live anymore. I'm thinking about ending it all."
    message.from_user = MagicMock()
    message.from_user.id = 12345
    message.from_user.username = "testuser"
    message.from_user.first_name = "Test"
    message.from_user.last_name = "User"
    message.from_user.language_code = "en"
    message.chat = MagicMock()
    message.chat.id = 12345
    message.answer = AsyncMock()
    message.bot = MagicMock()
    message.bot.send_chat_action = AsyncMock()

    # Create a mock user
    user = MagicMock(spec=UserModel)
    user.id = 12345
    user.can_send_message.return_value = True
    user.increment_message_count = AsyncMock()
    user.update_emotional_profile = AsyncMock()

    # Test with crisis intervention response
    with patch("app.handlers.message.generate_ai_response") as mock_generate_response:
        mock_generate_response.return_value = (
            "I'm really concerned about you and want to help. Please immediately contact a crisis helpline.",
            20,
            "test-model",
            0.1,
        )

        # Mock session context manager properly
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        with patch("app.handlers.message.get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Mock the get_recent_conversation_history function
            with patch(
                "app.services.conversation_service.get_recent_conversation_history"
            ) as mock_get_history:
                mock_get_history.return_value = []

                # Test successful execution
                await handle_text_message(message, user, "en")

                # Verify that the message was processed with appropriate response
                message.answer.assert_called_with(
                    "I'm really concerned about you and want to help. Please immediately contact a crisis helpline."
                )


@pytest.mark.asyncio
async def test_mature_content_handling() -> None:
    """Test handling of mature content."""
    # Create a mock message with mature content
    message = MagicMock(spec=Message)
    message.text = "I need advice about my intimate relationship."
    message.from_user = MagicMock()
    message.from_user.id = 12345
    message.from_user.username = "testuser"
    message.from_user.first_name = "Test"
    message.from_user.last_name = "User"
    message.from_user.language_code = "en"
    message.chat = MagicMock()
    message.chat.id = 12345
    message.answer = AsyncMock()
    message.bot = MagicMock()
    message.bot.send_chat_action = AsyncMock()

    # Create a mock user
    user = MagicMock(spec=UserModel)
    user.id = 12345
    user.can_send_message.return_value = True
    user.increment_message_count = AsyncMock()
    user.update_emotional_profile = AsyncMock()

    # Test with mature content response
    with patch("app.handlers.message.generate_ai_response") as mock_generate_response:
        mock_generate_response.return_value = (
            "I understand you need advice about intimate relationships. Let me provide some factual information.",
            15,
            "test-model",
            0.1,
        )

        # Mock session context manager properly
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        with patch("app.handlers.message.get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Mock the get_recent_conversation_history function
            with patch(
                "app.services.conversation_service.get_recent_conversation_history"
            ) as mock_get_history:
                mock_get_history.return_value = []

                # Test successful execution
                await handle_text_message(message, user, "en")

                # Verify that the message was processed with appropriate response
                message.answer.assert_called_with(
                    "I understand you need advice about intimate relationships. Let me provide some factual information."
                )


@pytest.mark.asyncio
async def test_content_filtering_and_emotional_profiling_integration() -> None:
    """Test combination of content filtering and emotional profiling."""
    # Create middleware instances
    content_filter = ContentFilterMiddleware()
    emotional_profiling = EmotionalProfilingMiddleware()

    # Create a mock user
    user = MagicMock(spec=UserModel)
    user.id = 12345
    user.emotional_traits = {}
    user.update_emotional_profile = AsyncMock()

    # Test processing a message with both emotional content and clean content
    message = MagicMock(spec=Message)
    message.text = "I'm feeling sad about my work situation. The weather is nice today."
    message.from_user = MagicMock()
    message.from_user.id = 12345
    message.answer = AsyncMock()

    # First, content filtering should allow the message
    filter_result = await content_filter._filter_content(message)
    assert filter_result is True

    # Then, emotional profiling should process the message
    data = {"user": user}
    profiling_result = await emotional_profiling.process_message(message, data)
    assert profiling_result is True

    # Verify that update_emotional_profile was called
    user.update_emotional_profile.assert_called_once()
