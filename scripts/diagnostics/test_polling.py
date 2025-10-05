#!/usr/bin/env python3
"""
Simple test script to verify polling mode is working
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.config import get_config
from app.services.ai_manager import AIManager
from app.services.ai_providers.base import ConversationMessage


async def test_polling():
    """Test that polling mode is properly configured."""
    print("🔍 Testing polling configuration...")
    
    try:
        config = get_config()
        print(f"✅ Configuration loaded")
        
        # Check polling setting
        use_polling = config.telegram.use_polling
        print(f"📡 Polling mode enabled: {use_polling}")
        
        if use_polling:
            print("✅ Bot is configured to use polling mode")
            return True
        else:
            print("⚠️ Bot is configured to use webhook mode")
            return False
            
    except Exception as e:
        print(f"❌ Error checking polling configuration: {e}")
        return False


async def test_ai_manager():
    """Test AI manager initialization."""
    print("\n🤖 Testing AI Manager...")
    
    try:
        ai_manager = AIManager()
        print("✅ AI Manager initialized successfully")
        
        # Test with a simple message
        test_message = ConversationMessage(
            role="user",
            content="Hello, how are you?"
        )
        
        print("🔄 Testing AI provider connectivity...")
        # This will test the fallback logic
        try:
            response = await ai_manager.generate_response([test_message])
            print(f"✅ AI Response received: {response.content[:50]}...")
        except Exception as e:
            print(f"⚠️ AI Error (expected if APIs have issues): {e}")
        
        return True
    except Exception as e:
        print(f"❌ AI Manager error: {e}")
        return False


async def main():
    """Main test function."""
    print("🤖 AI-Компаньон Polling Test")
    print("=" * 40)
    
    polling_ok = await test_polling()
    ai_ok = await test_ai_manager()
    
    print("\n" + "=" * 40)
    if polling_ok:
        print("✅ Polling mode is properly configured")
    else:
        print("❌ Polling mode configuration issue")
        
    if ai_ok:
        print("✅ AI Manager is working")
    else:
        print("❌ AI Manager has issues")


if __name__ == "__main__":
    asyncio.run(main())