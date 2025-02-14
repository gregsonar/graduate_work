from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (AsyncSession, create_async_engine,
                                    async_sessionmaker)
from sqlalchemy.ext.asyncio.session import Session
from sqlalchemy.orm import declarative_base, sessionmaker

from billing.src.core.config import settings

Base = declarative_base()

engine = create_async_engine(settings.dsn, echo=True, future=True)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session() -> Session:
    sync_engine = create_engine(settings.dsn_sync, future=True)
    sync_session = sessionmaker(
        bind=sync_engine,
        class_=Session,
        expire_on_commit=False,
    )
    with sync_session() as session:
        return session
