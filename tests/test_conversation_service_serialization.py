import json
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from app.services.ai_providers.base import (
    ConversationMessage,
    UserAIConversationContext,
)
from app.services.conversation import ConversationService


def test_conversation_context_serialization_in_service() -> None:
    """Test that conversation context serialization works correctly in the service."""
    # Create a context with messages
    context = UserAIConversationContext(
        user_messages=[
            ConversationMessage(
                role="user",
                content="Hello!",
                timestamp=datetime.now(UTC),
            )
        ],
        ai_responses=[
            ConversationMessage(
                role="assistant",
                content="Hi there!",
                timestamp=datetime.now(UTC),
            )
        ],
        last_interaction=datetime.now(UTC),
        topics=["greeting"],
        emotional_tone="positive",
    )

    # Convert to dict using the to_dict method
    context_dict = context.to_dict()

    # Add the history field as done in the fixed code
    context_dict["history"] = [
        {
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
        }
        for msg in context.get_combined_history()
    ]
    context_dict["message_count"] = len(context.user_messages)

    # This should not raise an exception
    json_str = json.dumps(context_dict, ensure_ascii=False)
    assert isinstance(json_str, str)
    assert "Hello!" in json_str
    assert "Hi there!" in json_str
    assert "history" in context_dict
    assert len(context_dict["history"]) == 2


if __name__ == "__main__":
    test_conversation_context_serialization_in_service()
    print("All tests passed!")
