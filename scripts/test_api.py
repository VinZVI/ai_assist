#!/usr/bin/env python3
"""
Test script to verify that the AI APIs are working properly
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import get_config
from app.services.ai_manager import AIManager
from app.services.ai_providers.base import ConversationMessage


async def test_apis() -> None:
    """Test the AI APIs"""
    print("🔍 Testing AI APIs...")

    # Load configuration
    config = get_config()
    print("✅ Configuration loaded successfully")

    # Test OpenRouter configuration
    print(f"🔑 OpenRouter API Key configured: {config.openrouter.is_configured()}")
    print(f"🌐 OpenRouter Base URL: {config.openrouter.openrouter_base_url}")
    print(f"🤖 OpenRouter Model: {config.openrouter.openrouter_model}")

    # Test AI Manager
    print("\n🤖 Testing AI Manager...")
    ai_manager = AIManager()

    # Test providers
    for provider_name, provider in ai_manager._providers.items():
        print(f"  🔧 {provider_name} provider configured: {provider.is_configured()}")

    # Test with a simple message
    print("\n💬 Testing AI response generation...")
    test_messages = [
        ConversationMessage(
            role="user",
            content="Hello, how are you?",
        ),
    ]

    try:
        response = await ai_manager.generate_response(test_messages)
        print("  ✅ Response generated successfully")
        print(f"  🤖 Provider: {response.provider}")
        print(f"  📝 Response: {response.content[:100]}...")
        print(f"  🧮 Tokens used: {response.tokens_used}")
        print(f"  🕐 Response time: {response.response_time:.2f}s")
    except Exception as e:
        print(f"  ❌ Error generating response: {e}")

    print("\n✅ API test completed")


if __name__ == "__main__":
    asyncio.run(test_apis())
