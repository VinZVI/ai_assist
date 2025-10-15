#!/usr/bin/env python3
"""
Simple test script to validate caching functionality
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.cache_service import MemoryCache
from app.models.user import User


async def test_memory_cache():
    """Test MemoryCache functionality"""
    print("Testing MemoryCache...")

    # Create a cache instance
    cache = MemoryCache(ttl_seconds=5, max_size=10)

    # Create a test user
    user = User(
        id=1,
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        language_code="en",
    )

    # Test setting a user in cache
    await cache.set(user)
    print("✓ User set in cache")

    # Test getting a user from cache
    cached_user = await cache.get(123456789)
    if cached_user:
        print("✓ User retrieved from cache")
        print(
            f"  User: {cached_user.username} ({cached_user.first_name} {cached_user.last_name})"
        )
    else:
        print("✗ Failed to retrieve user from cache")
        return False

    # Test cache stats
    stats = cache.get_stats()
    print(f"✓ Cache stats: {stats}")

    # Test cache miss
    missing_user = await cache.get(999999999)
    if missing_user is None:
        print("✓ Cache correctly returned None for missing user")
    else:
        print("✗ Cache should have returned None for missing user")
        return False

    return True


async def main():
    """Main test function"""
    print("Starting caching tests...")

    try:
        result = await test_memory_cache()
        if result:
            print("\n✓ All tests passed!")
            return 0
        else:
            print("\n✗ Some tests failed!")
            return 1
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
