#!/usr/bin/env python3
"""
Diagnostic script to check API connectivity for OpenRouter
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.config import get_config
from app.services.ai_providers.openrouter import OpenRouterProvider


async def check_openrouter_api() -> bool | None:
    """Check OpenRouter API connectivity."""
    print("🔍 Checking OpenRouter API connectivity...")

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


async def main() -> None:
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

    # Check OpenRouter API
    openrouter_ok = await check_openrouter_api()

    print("\n" + "=" * 50)
    if openrouter_ok:
        print("🎉 OpenRouter API is working correctly!")
    else:
        print(
            "💥 OpenRouter API is not accessible - check your API key and network connectivity"
        )

    print("\n💡 Recommendations:")
    print("  - Check your OpenRouter API key")
    print("  - Verify the API key is correct in .env")


if __name__ == "__main__":
    asyncio.run(main())
