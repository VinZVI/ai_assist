import os
from app.config import DatabaseConfig

# Clear any existing environment variables that might interfere
if 'DATABASE_URL' in os.environ:
    del os.environ['DATABASE_URL']
if 'DATABASE_HOST' in os.environ:
    del os.environ['DATABASE_HOST']
if 'DATABASE_PORT' in os.environ:
    del os.environ['DATABASE_PORT']
if 'DATABASE_NAME' in os.environ:
    del os.environ['DATABASE_NAME']
if 'DATABASE_USER' in os.environ:
    del os.environ['DATABASE_USER']
if 'DATABASE_PASSWORD' in os.environ:
    del os.environ['DATABASE_PASSWORD']

print("=== Test: DatabaseConfig with constructor parameters ===")
try:
    config = DatabaseConfig(
        database_host="localhost",
        database_port=5432,
        database_name="test_db",
        database_user="test_user",
        database_password="test_password"
    )
    print(f"database_host: {config.database_host}")
    print(f"database_port: {config.database_port}")
    print(f"database_name: {config.database_name}")
    print(f"database_user: {config.database_user}")
    print(f"database_password: {config.database_password}")
    print(f"database_url: {config.database_url}")
    
    expected_url = "postgresql+asyncpg://test_user:test_password@localhost:5432/test_db"
    print(f"Expected URL: {expected_url}")
    print(f"URLs match: {config.database_url == expected_url}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()