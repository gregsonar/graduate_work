import os
import sys
from logging.config import fileConfig
import asyncio

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from auth.core.config import config as cf
from auth.models.user import User
from auth.models.role import Role
from auth.models.user_role import UserRole
from auth.models.access_log import AccessLog
from auth.models.user_account import UserSocialAccount

load_dotenv()


config = context.config


def get_database_url():
    db_url = f"postgresql+asyncpg://{cf.db_user}:{cf.db_password}@{cf.db_host}:{cf.db_port}/{cf.db_name}"
    print(f"Database URL: {db_url}")
    return db_url


if config.config_file_name is not None:
    fileConfig(config.config_file_name)

metadata = MetaData()
# Добавляем метаданные всех моделей
for model in [User, Role, UserRole, AccessLog, UserSocialAccount]:
    for table in model.metadata.tables.values():
        if table.name not in metadata.tables:
            table.to_metadata(metadata)

target_metadata = metadata


def run_migrations_offline() -> None:
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    url = get_database_url()

    connectable = create_async_engine(url)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()