from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from .utils import logout_from_auth_service


def custom_logout(request):
    """Кастомный обработчик логаута"""
    # Логаут из внешнего сервиса
    access_token = request.session.get("access_token")
    refresh_token = request.session.get("refresh_token")

    if access_token and refresh_token:
        logout_from_auth_service(access_token, refresh_token)

    # Очищаем сессию и делаем логаут Django
    request.session.flush()
    logout(request)

    return redirect(reverse("admin:login"))
