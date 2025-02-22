import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from subscriptions.core.config import settings
from subscriptions.models.base_models import Base
from subscriptions.models.subscription import (
    Subscription,
    SubscriptionStatus,
    SubscriptionPlanType,
)


@pytest.fixture(scope="session")
def event_loop():
    import asyncio

    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(db_engine):
    async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def active_subscription(db_session):
    subscription = Subscription(
        id=uuid4(),
        user_id=uuid4(),
        plan_type=SubscriptionPlanType.BASIC,
        status=SubscriptionStatus.ACTIVE,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        price=9.99,
        is_auto_renewable=True,
    )
    db_session.add(subscription)
    await db_session.commit()
    return subscription
