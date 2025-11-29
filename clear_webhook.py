#!/usr/bin/env python3
"""Script to clear webhook settings."""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from aiogram import Bot

from app.config import get_config


async def clear_webhook():
    """Clear webhook settings."""
    try:
        config = get_config()
        bot = Bot(token=config.telegram.bot_token)
        await bot.delete_webhook(drop_pending_updates=True)
        print('Webhook cleared successfully')
        await bot.session.close()
    except Exception as e:
        print(f"Error clearing webhook: {e}")


if __name__ == "__main__":
    asyncio.run(clear_webhook())
