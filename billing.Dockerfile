FROM python:3.12-slim

WORKDIR /app


RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей
COPY billing/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем содержимое billing в /app/billing
COPY ./billing /app/billing/

# Копируем содержимое payments в /app/payments
COPY ./payments /app/payments/

# Устанавливаем переменную окружения для Python path
ENV PYTHONPATH=/app

EXPOSE 8000

# Переходим в директорию с исходным кодом
WORKDIR /app/payments

# Команда для запуска приложения
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]