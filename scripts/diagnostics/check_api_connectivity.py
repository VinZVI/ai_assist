#!/usr/bin/env python3
"""
Diagnostic script to check API connectivity for both DeepSeek and OpenRouter
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.config import get_config
from app.services.ai_providers.deepseek import DeepSeekProvider
from app.services.ai_providers.openrouter import OpenRouterProvider


async def check_deepseek_api():
    """Check DeepSeek API connectivity."""
    print("🔍 Checking DeepSeek API connectivity...")

    try:
        config = get_config()
        print(f"  API Key configured: {config.deepseek.is_configured()}")
        print(f"  Base URL: {config.deepseek.deepseek_base_url}")
        print(f"  Model: {config.deepseek.deepseek_model}")

        if not config.deepseek.is_configured():
            print("  ❌ DeepSeek API key not configured properly")
            return False

        provider = DeepSeekProvider()
        health = await provider.health_check()

        if health["status"] == "healthy":
            print("  ✅ DeepSeek API is accessible")
            return True
        print(f"  ❌ DeepSeek API error: {health.get('error', 'Unknown error')}")
        return False

    except Exception as e:
        print(f"  ❌ DeepSeek API error: {e}")
        return False


async def check_openrouter_api():
    """Check OpenRouter API connectivity."""
    print("\n🔍 Checking OpenRouter API connectivity...")

    try:
        config = get_config()
        print(f"  API Key configured: {config.openrouter.is_configured()}")
        print(f"  Base URL: {config.openrouter.openrouter_base_url}")
        print(f"  Model: {config.openrouter.openrouter_model}")

        if not config.openrouter.is_configured():
            print("  ❌ OpenRouter API key not configured properly")
            return False

        provider = OpenRouterProvider()
        health = await provider.health_check()

        if health["status"] == "healthy":
            print("  ✅ OpenRouter API is accessible")
            return True
        print(f"  ❌ OpenRouter API error: {health.get('error', 'Unknown error')}")
        return False

    except Exception as e:
        print(f"  ❌ OpenRouter API error: {e}")
        return False


async def main():
    """Main diagnostic function."""
    print("🤖 AI-Компаньон API Diagnostic Tool")
    print("=" * 50)

    # Load config
    try:
        get_config()
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return

    # Check both APIs
    deepseek_ok = await check_deepseek_api()
    openrouter_ok = await check_openrouter_api()

    print("\n" + "=" * 50)
    if deepseek_ok and openrouter_ok:
        print("🎉 All APIs are working correctly!")
    elif deepseek_ok or openrouter_ok:
        print("⚠️  One API is working, but fallback may be needed")
    else:
        print(
            "💥 No APIs are accessible - check your API keys and network connectivity"
        )

    print("\n💡 Recommendations:")
    if not deepseek_ok:
        print("  - Check your DeepSeek API key balance")
        print("  - Verify the API key is correct in .env")
    if not openrouter_ok:
        print("  - Check your OpenRouter API key")
        print("  - Verify the API key is correct in .env")


if __name__ == "__main__":
    asyncio.run(main())
