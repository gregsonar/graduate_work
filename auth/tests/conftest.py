import os
import sys
import pytest
from typing import AsyncGenerator, Generator
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import uuid
from unittest.mock import AsyncMock, MagicMock
from pydantic_settings import BaseSettings

from redis.asyncio import Redis
from async_fastapi_jwt_auth import AuthJWT

from auth.core.breaker import AsyncCircuitBreaker
from auth.services.auth_service import AuthService
from auth.db.redis_db import get_redis, redis

from auth.services.token_service import TokenService

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from auth.models.role import Role
from auth.models.user import User
from auth.models.user_role import UserRole
from auth.db.postgres import Base

# Настройки тестовой базы данных
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test_db"

pytest_plugins = ("pytest_asyncio",)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="session")
async def create_tables_old(engine: AsyncEngine) -> None:
    """Прошлая версия фикстуры"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all, checkfirst=True)
        await conn.run_sync(Base.metadata.create_all)

@pytest.fixture(scope="session")
async def create_tables(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        #await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

@pytest.fixture(scope="function")
async def db_session(engine: AsyncEngine, create_tables: None) -> AsyncGenerator[AsyncSession, None]:
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session

@pytest.fixture
def mock_role():
    return Role(
        id=uuid.UUID("f49ebc90-caef-4f19-822b-8fd5a570e057"),
        name="user",
        description="user"
    )

@pytest.fixture
def mock_user():
    return User(
        id=uuid.UUID("4e4734c1-3359-447e-9f7c-31d8b76e1ffb"),
        password="admin",
        username="test_user",
        is_superuser=True
    )

@pytest.fixture
def mock_user_role(mock_user, mock_role):
    return UserRole(
        user_id=mock_user.id,
        role_id=mock_role.id
    )

@pytest.fixture
def mock_query_result():
    class MockResult:
        def __init__(self, return_value=None):
            self._return_value = return_value

        def scalar_one_or_none(self):
            return self._return_value

        def scalars(self):
            result = MagicMock()
            result.all.return_value = self._return_value
            return result

    return MockResult

@pytest.fixture
def create_user_role():
    def _create_user_role(user_id, role_id):
        return UserRole(
            user_id=user_id,
            role_id=role_id
        )
    return _create_user_role

@pytest.fixture
def mock_db_error():
    return Exception("Database error")


@pytest.fixture
def mock_redis_client():
    client = AsyncMock(spec=Redis)

    # Создаем мок для pipeline
    pipeline_mock = AsyncMock()
    pipeline_mock.set = AsyncMock(return_value=pipeline_mock)
    pipeline_mock.execute = AsyncMock(return_value=[True, True])

    # Настраиваем основные методы Redis
    async def mock_get(key: str):
        # По умолчанию возвращаем None для всех ключей
        return None

    async def mock_set(*args, **kwargs):
        return True

    async def mock_incr(key: str):
        return 1

    async def mock_setex(key: str, expires: int, value: str):
        return True

    client.get = AsyncMock(side_effect=mock_get)
    client.set = AsyncMock(side_effect=mock_set)
    client.setex = AsyncMock(side_effect=mock_setex)
    client.incr = AsyncMock(side_effect=mock_incr)
    client.delete = AsyncMock(return_value=True)

    # Настраиваем pipeline
    client.pipeline = AsyncMock(return_value=pipeline_mock)

    return client

@pytest.fixture
def token_service(mock_redis_client, mock_session):
    service = TokenService(mock_redis_client, mock_session)
    service.config.secret_key = "test_secret_key"
    service.config.algorithm = "HS256"
    service.config.access_token_expire_minutes = 30
    service.config.refresh_token_expire_days = 7
    return service


@pytest.fixture
async def circuit_breaker(mock_redis_client):
    return AsyncCircuitBreaker(
        redis=mock_redis_client,
        service_name="test_service",
        failure_threshold=3,
        recovery_timeout=1,
        half_open_max_tries=2
    )

@pytest.fixture
def mock_service():
    class Service:
        def __init__(self):
            self.call_count = 0
            self.should_fail = False

        async def test_operation(self, user_id: str = "test_user"):
            self.call_count += 1
            if self.should_fail:
                raise Exception("Service error")
            return {"access_token": "test_token", "refresh_token": "refresh"}

    return Service()

@pytest.fixture
async def redis_client() -> AsyncGenerator[Redis, None]:
    """Create Redis client for tests"""
    redis_url = "redis://localhost:6379/1"  # Используем базу 1 для тестов
    client = Redis.from_url(redis_url, decode_responses=True)
    try:
        await client.ping()  # Проверяем подключение
        await client.flushdb()  # Очищаем тестовую базу
        yield client
    finally:
        await client.flushdb()
        await client.close()

@pytest.fixture
async def context_redis_client():
    client = AsyncMock(spec=Redis)

    # Создаем мок для pipeline с поддержкой async context manager
    pipeline_mock = AsyncMock()
    pipeline_mock.__aenter__ = AsyncMock(return_value=pipeline_mock)
    pipeline_mock.__aexit__ = AsyncMock(return_value=False)
    pipeline_mock.incr = AsyncMock(return_value=pipeline_mock)
    pipeline_mock.expire = AsyncMock(return_value=pipeline_mock)
    pipeline_mock.execute = AsyncMock(return_value=[1, True])  # default values

    # Настраиваем pipeline для возврата правильного async context manager
    client.pipeline.return_value = pipeline_mock

    return client