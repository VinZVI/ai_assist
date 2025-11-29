#!/usr/bin/env python3
"""Script to check users in the database."""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select

from app.database import get_session, init_db
from app.models.user import User


async def check_users():
    """Check users in the database."""
    try:
        # Initialize the database
        await init_db()

        async with get_session() as session:
            # Get all users
            stmt = select(User)
            result = await session.execute(stmt)
            users = result.scalars().all()

            print(f"Found {len(users)} users:")
            for user in users:
                print(f"  ID: {user.id}, Telegram ID: {user.telegram_id}")
                print(f"    Verification status: {user.verification_status}")
                print(f"    Is fully verified: {user.is_fully_verified}")
                print(f"    Age verified: {user.age_verified}")
                print(f"    Terms accepted: {user.terms_accepted}")
                print(f"    Privacy policy accepted: {user.privacy_policy_accepted}")
                print(f"    Community guidelines accepted: {user.community_guidelines_accepted}")
                print()
    except Exception as e:
        print(f"Error checking users: {e}")


if __name__ == "__main__":
    asyncio.run(check_users())
