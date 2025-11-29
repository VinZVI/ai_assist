import importlib.util
import os
import sys

import psycopg2

# Import the config module directly from the file to avoid circular imports
spec = importlib.util.spec_from_file_location("config", os.path.join(os.path.dirname(__file__), "app", "config.py"))
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
get_config = config_module.get_config

def main():
    config = get_config()
    # Convert asyncpg URL to psycopg2 URL
    db_url = config.database.database_url.replace('postgresql+asyncpg://', 'postgresql://')

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    # Check tables
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cur.fetchall()

    print('Tables in database:')
    for table in tables:
        print(f'  - {table[0]}')

    # Check applied migrations
    try:
        cur.execute("SELECT * FROM alembic_version")
        versions = cur.fetchall()
        print('\nApplied migrations:')
        for version in versions:
            print(f'  - {version[0]}')
    except psycopg2.Error as e:
        print(f'\nNo alembic_version table found or error: {e}')

    # Check if payments table exists and what columns it has
    try:
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'payments'")
        columns = cur.fetchall()
        print('\nColumns in payments table:')
        for column in columns:
            print(f'  - {column[0]}')
    except psycopg2.Error as e:
        print(f'\nError checking payments table: {e}')

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
