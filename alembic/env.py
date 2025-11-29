import os

# Import the database configuration from the app
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import the config module directly from the file
import importlib.util

spec = importlib.util.spec_from_file_location("config", os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "config.py"))
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
get_config = config_module.get_config

# Import models
from app.models.character import Character
from app.models.character_rating import CharacterRating
from app.models.character_tag import CharacterTag
from app.models.chat import Chat
from app.models.chat_message import ChatMessage
from app.models.scenario import Scenario
from app.models.subscription import Subscription, SubscriptionUsage
from app.models.user import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set the database URL from the app configuration (use synchronous URL for Alembic)
app_config = get_config()
# Convert asyncpg URL to psycopg2 URL for Alembic
database_url = app_config.database.database_url
if database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
