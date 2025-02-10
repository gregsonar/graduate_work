FROM python:3.12-slim

WORKDIR /app


RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем содержимое subscriptions в /app/subscriptions
COPY . /app/subscriptions/

# Устанавливаем переменную окружения для Python path
ENV PYTHONPATH=/app

EXPOSE 8000

# Переходим в директорию с исходным кодом
WORKDIR /app/subscriptions

# Команда для запуска приложения через gunicorn
CMD ["gunicorn", "-c", "gunicorn_config.py", "main:app"]