from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import IntegrityError
import os
import requests
from dotenv import load_dotenv

load_dotenv()


class Command(BaseCommand):
    help = 'Creates a superuser if one does not exist'

    def handle(self, *args, **options):
        username = os.getenv('DJANGO_SUPERUSER_USERNAME')
        email = os.getenv('DJANGO_SUPERUSER_EMAIL')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD')

        if not username or not email or not password:
            self.stdout.write(self.style.ERROR('Environment variables for superuser are not set properly.'))
            return

        try:
            # Проверяем существование пользователя перед созданием
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'Superuser {username} already exists.'))
                return

            # Регистрируем пользователя во внешнем сервисе
            auth_service_url = os.getenv('AUTH_SERVICE_URL', 'http://auth_api:8000/api/v1')
            register_url = f"{auth_service_url}/auth/register"
            response = requests.post(
                register_url,
                json={
                    "username": username,
                    "email": email,
                    "password": password,
                    "is_superuser": True
                }
            )

            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS(f'Superuser {username} registered successfully in auth service.'))

                # Только после успешной регистрации в Auth сервисе создаем пользователя в Django
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                self.stdout.write(self.style.SUCCESS(f'Superuser {username} created successfully in Django.'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to register superuser in auth service: {response.text}'))

        except IntegrityError as e:
            self.stdout.write(self.style.ERROR(f'Failed to create superuser: {str(e)}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))