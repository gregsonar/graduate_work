import requests
from typing import Optional
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.conf import settings
from .utils import AuthServiceError


class ExternalAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None) -> Optional[User]:
        """Аутентификация через внешний сервис"""
        try:
            # Получаем токены
            response = requests.post(
                f"{settings.AUTH_SERVICE_URL}/auth/login",
                json={"username": username, "password": password}
            )

            if response.status_code == 200:
                tokens = response.json()
                request.session['access_token'] = tokens['access_token']
                request.session['refresh_token'] = tokens['refresh_token']

                # Получаем данные пользователя
                user_response = requests.get(
                    f"{settings.AUTH_SERVICE_URL}/auth/me",
                    params={'token': tokens['access_token']}
                )

                if user_response.status_code != 200:
                    raise AuthServiceError("Failed to get user data from auth service")

                user_data = user_response.json()

                # Проверяем наличие email
                email = user_data.get('email')
                if not email:
                    # Если email не получен от сервиса аутентификации,
                    # пытаемся найти существующего пользователя
                    try:
                        existing_user = User.objects.get(username=username)
                        email = existing_user.email
                    except User.DoesNotExist:
                        # Если пользователь не существует, используем дефолтный email
                        email = f"{username}@example.com"  # временное решение

                # Создаем или обновляем пользователя Django
                user, _ = User.objects.update_or_create(
                    username=username,
                    defaults={
                        'is_staff': True,  # Для доступа к админке
                        'is_superuser': user_data.get('is_superuser', False),
                        'email': email
                    }
                )
                return user

        except requests.RequestException as e:
            raise AuthServiceError(f"Authentication failed: {str(e)}")

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None