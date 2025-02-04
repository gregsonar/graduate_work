import os
import sys
from logging.config import fileConfig
import asyncio

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from subscriptions.models import (Subscription, SubscriptionHistory,
                                  SubscriptionPlan, UserSubscription, UserSubscriptionHistory)

from subscriptions.models.base_models import Base

from subscriptions.core.config import settings as cf
load_dotenv()


config = context.config


def get_database_url():
    db_url = f'postgresql+asyncpg://{cf.POSTGRES_USER}:{cf.POSTGRES_PASSWORD}@{cf.POSTGRES_HOST}:{cf.POSTGRES_PORT}/{cf.POSTGRES_DB}'
    print(f"Database URL: {db_url}")
    return db_url


if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# metadata = MetaData()
# # Добавляем метаданные всех моделей
# for model in [Subscription, SubscriptionHistory, SubscriptionPlan, UserSubscription, UserSubscriptionHistory]:
#     for table in model.metadata.tables.values():
#         if table.name not in metadata.tables:
#             table.to_metadata(metadata)


target_metadata = Base.metadata


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