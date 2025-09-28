#!/usr/bin/env python3
"""
Debug script to test generate_ai_response function
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.user import User
from app.services.ai_providers.base import AIResponse


async def test_generate_ai_response_success() -> None:
    """Test the generate_ai_response function success case"""
    # Arrange
    mock_user = User(
        id=1,
        telegram_id=123456,
        username="testuser",
        first_name="Test",
        last_name="User",
        daily_message_count=5,
        is_premium=False,
    )
    user_message = "Hello, AI!"

    # Mock AI response
    mock_ai_response = AIResponse(
        content="Hello, user!",
        model="test-model",
        provider="test-provider",
        tokens_used=10,
        response_time=0.5,
    )

    with patch("app.handlers.message.get_ai_manager") as mock_get_ai_manager:
        mock_manager = AsyncMock()
        mock_get_ai_manager.return_value = mock_manager
        mock_manager.generate_response.return_value = mock_ai_response

        with patch(
            "app.handlers.message.get_recent_conversation_history"
        ) as mock_get_history:
            mock_get_history.return_value = []

            # Act
            from app.handlers.message import generate_ai_response

            result = await generate_ai_response(mock_user, user_message)
            print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(test_generate_ai_response_success())
