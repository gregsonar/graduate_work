from typing import Dict, Any
import requests
from django.conf import settings


class AuthServiceError(Exception):
    """Ошибка взаимодействия с сервисом авторизации"""

    pass


def make_auth_request(method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    url = f"{settings.AUTH_SERVICE_URL}/{endpoint.lstrip('/')}"

    try:
        response = requests.request(
            method, url, timeout=settings.AUTH_SERVICE_TIMEOUT, **kwargs
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise AuthServiceError(f"Auth service request failed: {str(e)}")


def logout_from_auth_service(access_token: str, refresh_token: str) -> None:
    try:
        make_auth_request(
            "POST",
            "/auth/logout",
            params={"access_token": access_token, "refresh_token": refresh_token},
        )
    except AuthServiceError:
        pass
