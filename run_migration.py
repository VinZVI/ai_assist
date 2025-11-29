import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

from alembic.config import Config
from alembic import command
from app.config import get_config


def run_migration():
    # Create alembic config
    alembic_cfg = Config("alembic.ini")

    # Set the database URL from app config
    app_config = get_config()
    # Convert asyncpg URL to psycopg2 URL for Alembic
    database_url = app_config.database.database_url
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    # Run the migration
    try:
        command.upgrade(alembic_cfg, "head")
        print("Migrations applied successfully!")
    except Exception as e:
        print(f"Error applying migrations: {e}")
        print("\nNote: Alembic requires psycopg2 for PostgreSQL migrations.")
        print("Install it with: pip install psycopg2-binary")
        raise


if __name__ == "__main__":
    run_migration()
