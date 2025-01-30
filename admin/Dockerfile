FROM python:3.12

WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE 'admin.settings'

RUN groupadd -r web && useradd -r -g web web
COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN  mkdir -p /var/www/static/ \
     && mkdir -p /var/www/media/ \
     && mkdir -p /opt/app/static/ \
     && mkdir -p /opt/app/media/ \
     && pip install --upgrade pip \
     && pip install -r requirements.txt

COPY . .

RUN chown -R web:web /opt/app

USER web

EXPOSE 8000

RUN chown -R web:web /opt/app/static

CMD ["sh", "-c", "python manage.py makemigrations \
                    &&python manage.py migrate \
                    && python manage.py create_superuser \
                    && python manage.py collectstatic --no-input \
                    && gunicorn -c gunicorn_config.py admin.wsgi:application"]

