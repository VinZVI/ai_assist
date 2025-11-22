import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(__file__))

from alembic.config import Config
from alembic import command
from app.config import get_config

def run_migration():
    # Create alembic config
    alembic_cfg = Config("alembic.ini")
    
    # Set the database URL from app config
    app_config = get_config()
    alembic_cfg.set_main_option('sqlalchemy.url', app_config.database.database_url)
    
    # Run the migration
    command.upgrade(alembic_cfg, "head")

if __name__ == "__main__":
    run_migration()