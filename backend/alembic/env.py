import sys
import os
from logging.config import fileConfig

from sqlalchemy import pool
from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.config import get_engine, Base
from dotenv import load_dotenv
load_dotenv()

# This import is critical — it tells Alembic about all our tables
import database.models

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = os.environ.get("DATABASE_URL")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = get_engine()
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