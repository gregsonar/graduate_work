import requests
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

from .utils import AuthServiceError


class AuthTokenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                self._validate_or_refresh_tokens(request)
            except AuthServiceError:
                logout(request)
                return redirect(reverse('admin:login'))

        response = self.get_response(request)
        return response

    def _validate_or_refresh_tokens(self, request):
        """Проверка и обновление токенов"""
        access_token = request.session.get('access_token')
        refresh_token = request.session.get('refresh_token')

        if not access_token or not refresh_token:
            raise AuthServiceError("No tokens found")

        try:
            # Проверяем валидность access token
            response = requests.get(
                f"{settings.AUTH_SERVICE_URL}/auth/me",
                params={'token': access_token}
            )

            if response.status_code != 200:
                # Пробуем обновить токены
                refresh_response = requests.post(
                    f"{settings.AUTH_SERVICE_URL}/auth/refresh",
                    params={'refresh_token': refresh_token}
                )

                if refresh_response.status_code == 200:
                    tokens = refresh_response.json()
                    request.session['access_token'] = tokens['access_token']
                    request.session['refresh_token'] = tokens['refresh_token']
                else:
                    raise AuthServiceError("Failed to refresh tokens")

        except requests.RequestException as e:
            raise AuthServiceError(f"Token validation failed: {str(e)}")