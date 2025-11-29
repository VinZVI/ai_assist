#!/usr/bin/env python3
"""Test script to verify onboarding router setup."""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.dependencies import container
from app.core.service_registry import initialize_services
from app.handlers.onboarding import setup_onboarding_handler


async def test_onboarding_setup():
    """Test onboarding router setup."""
    try:
        # Initialize services
        await initialize_services()

        # Get user service
        user_service = container.get("user_service")

        # Set up onboarding router
        router = await setup_onboarding_handler(user_service)

        print(f"Router name: {router.name}")
        print(f"Message handlers: {len(router.message.handlers)}")
        print(f"Callback query handlers: {len(router.callback_query.handlers)}")

        # Check callback query handlers
        for i, handler in enumerate(router.callback_query.handlers):
            print(f"Callback handler {i}: {handler.callback}")
            print(f"  Filters: {handler.filters}")

    except Exception as e:
        print(f"Error setting up onboarding: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_onboarding_setup())
