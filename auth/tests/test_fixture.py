import pytest
from async_fastapi_jwt_auth import AuthJWT


def test_authorize_fixture(authorize: AuthJWT):
    # Проверяем, что объект AuthJWT был корректно создан
    assert isinstance(authorize, AuthJWT)

    # Проверяем, что фиктивный запрос был установлен и содержит нужный заголовок
    assert authorize._request is not None
    assert authorize._request.headers.get("Authorization") == "Bearer testtoken"
