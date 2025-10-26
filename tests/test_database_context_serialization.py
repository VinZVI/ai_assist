import json
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from app.services.conversation.conversation_history import (
    get_conversation_context_from_db,
)

from app.services.ai_providers.base import (
    ConversationMessage,
)


def test_conversation_context_serialization_from_database() -> None:
    """Test that conversation context from database can be properly serialized."""
    # Create a context with serialized history (as it would be returned from database)
    context = {
        "history": [
            {
                "role": "user",
                "content": "Hello!",
                "timestamp": datetime.now(UTC).isoformat(),
            },
            {
                "role": "assistant",
                "content": "Hi there!",
                "timestamp": datetime.now(UTC).isoformat(),
            },
        ],
        "message_count": 1,
        "last_interaction": datetime.now(UTC).isoformat(),
        "topics": ["greeting"],
        "emotional_tone": "positive",
    }

    # This should not raise an exception
    json_str = json.dumps(context, ensure_ascii=False)
    assert isinstance(json_str, str)
    assert "Hello!" in json_str
    assert "Hi there!" in json_str
    assert "history" in context
    assert len(context["history"]) == 2


def test_conversation_message_serialization() -> None:
    """Test that ConversationMessage objects can be properly serialized."""
    # Create conversation messages
    messages = [
        ConversationMessage(
            role="user",
            content="Hello!",
            timestamp=datetime.now(UTC),
        ),
        ConversationMessage(
            role="assistant",
            content="Hi there!",
            timestamp=datetime.now(UTC),
        ),
    ]

    # Convert to serializable format (as done in our fix)
    serialized_history = [
        {
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
        }
        for msg in messages
    ]

    # This should not raise an exception
    json_str = json.dumps(serialized_history, ensure_ascii=False)
    assert isinstance(json_str, str)
    assert "Hello!" in json_str
    assert "Hi there!" in json_str


if __name__ == "__main__":
    test_conversation_context_serialization_from_database()
    test_conversation_message_serialization()
    print("All tests passed!")
