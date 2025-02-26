from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from httpx import AsyncClient

from auth.services.auth_service import AuthService


# Создаем тестовое приложение FastAPI для проверки AuthService
@pytest.fixture
def test_app(auth_service: AuthService):
    app = FastAPI()

    @app.post("/register")
    async def register(
        username: str, password: str, service: AuthService = Depends(auth_service)
    ):
        return await service.register_user(username, password)

    @app.post("/login")
    async def login(
        username: str, password: str, service: AuthService = Depends(auth_service)
    ):
        return await service.authenticate_user(username, password)

    @app.post("/logout")
    async def logout(token: str, service: AuthService = Depends(auth_service)):
        await service.logout_user(token)
        return {"message": "Successfully logged out"}

    @app.post("/refresh")
    async def refresh(token: str, service: AuthService = Depends(auth_service)):
        return {"access_token": await service.refresh_token(token)}

    return app


@pytest.mark.asyncio
async def test_register_user(test_app):
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.post(
            "/register", json={"username": "test_user", "password": "test_password"}
        )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["username"] == "test_user"


@pytest.mark.asyncio
async def test_login_user(test_app, auth_service):
    # Register a user first
    await auth_service.register_user("test_user", "test_password")

    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.post(
            "/login", json={"username": "test_user", "password": "test_password"}
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_logout_user(test_app, auth_service):
    # Register and login a user
    user_data = await auth_service.register_user("test_user", "test_password")
    tokens = await auth_service.authenticate_user("test_user", "test_password")
    access_token = tokens["access_token"]

    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.post("/logout", json={"token": access_token})
    assert response.status_code == 200
    assert response.json() == {"message": "Successfully logged out"}


@pytest.mark.asyncio
async def test_refresh_token(test_app, auth_service):
    # Register and login a user
    user_data = await auth_service.register_user("test_user", "test_password")
    tokens = await auth_service.authenticate_user("test_user", "test_password")
    refresh_token = tokens["refresh_token"]

    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.post("/refresh", json={"token": refresh_token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
