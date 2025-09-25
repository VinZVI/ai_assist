import os
from app.config import DatabaseConfig

# Check environment variables
print("=== Environment Variables ===")
env_vars = ['DATABASE_URL', 'DATABASE_HOST', 'DATABASE_PORT', 'DATABASE_NAME', 'DATABASE_USER', 'DATABASE_PASSWORD']
for var in env_vars:
    value = os.environ.get(var, 'Not set')
    if var == 'DATABASE_PASSWORD' and value != 'Not set':
        print(f"{var}: {'*' * len(value)}")
    else:
        print(f"{var}: {value}")

print("\n=== Creating DatabaseConfig with constructor parameters ===")
try:
    config = DatabaseConfig(
        database_host="localhost",
        database_port=5432,
        database_name="test_db",
        database_user="test_user",
        database_password="test_password"
    )
    
    print(f"Constructor parameters:")
    print(f"  database_host: {config.database_host}")
    print(f"  database_port: {config.database_port}")
    print(f"  database_name: {config.database_name}")
    print(f"  database_user: {config.database_user}")
    print(f"  database_password: {'*' * len(config.database_password)}")
    print(f"  database_url: {config.database_url}")
    
    expected_url = "postgresql+asyncpg://test_user:test_password@localhost:5432/test_db"
    print(f"\nExpected URL: {expected_url}")
    print(f"URLs match: {config.database_url == expected_url}")
    
    if config.database_url != expected_url:
        print(f"\nActual URL parts:")
        import urllib.parse
        parsed = urllib.parse.urlparse(config.database_url)
        print(f"  scheme: {parsed.scheme}")
        print(f"  username: {parsed.username}")
        print(f"  password: {'*' * len(parsed.password) if parsed.password else 'None'}")
        print(f"  hostname: {parsed.hostname}")
        print(f"  port: {parsed.port}")
        print(f"  path: {parsed.path}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()