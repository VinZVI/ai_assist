import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_providers.base import (
    ConversationMessage,
    UserAIConversationContext,
)
from app.services.conversation import ConversationService
from app.services.conversation.conversation_history import (
    get_conversation_context_from_db,
    get_recent_conversation_history,
)


@pytest.mark.asyncio
async def test_conversation_service_initialization() -> None:
    """Test that ConversationService initializes correctly."""
    service = ConversationService()
    assert service is not None
    assert not service._initialized


@pytest.mark.asyncio
async def test_conversation_service_initialize() -> None:
    """Test ConversationService initialization with container."""
    with patch(
        "app.services.conversation.conversation_service.container"
    ) as mock_container:
        mock_cache_service = Mock()
        mock_container.get.return_value = mock_cache_service

        service = ConversationService()
        await service.initialize()

        assert service._initialized
        assert service._cache_service == mock_cache_service
        mock_container.get.assert_called_once_with("cache_service")


@pytest.mark.asyncio
async def test_conversation_service_cache_service_property() -> None:
    """Test lazy initialization of cache_service property."""
    with patch(
        "app.services.conversation.conversation_service.container"
    ) as mock_container:
        mock_cache_service = Mock()
        mock_container.get.return_value = mock_cache_service

        service = ConversationService()
        # Access property twice to ensure lazy initialization works correctly
        cache_service1 = service.cache_service
        cache_service2 = service.cache_service

        assert cache_service1 == mock_cache_service
        assert cache_service2 == mock_cache_service
        # Should only call container.get once due to caching
        mock_container.get.assert_called_once_with("cache_service")


if __name__ == "__main__":
    test_conversation_service_initialization()
    test_conversation_service_initialize()
    test_conversation_service_cache_service_property()
    print("All tests passed!")
