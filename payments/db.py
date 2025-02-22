import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://user:password@localhost/payments_db"
)

# Создаём асинхронный движок SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Создаём фабрику асинхронных сессий, используя async_sessionmaker
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

# Базовый класс для моделей
Base = declarative_base()


# Dependency для получения сессии в FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
