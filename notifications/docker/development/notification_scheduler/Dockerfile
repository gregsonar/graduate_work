FROM python:3.10.2-buster

WORKDIR /usr/src/notification_scheduler

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip

COPY ./requirements.txt ./

RUN pip install -r ./requirements.txt

CMD cd .. && celery -A notification_scheduler  beat --loglevel=debug