FROM python:3.8-slim-bullseye

# RUN apt update && apt install -y procps gdb

ENV ANTAREST_CONF /resources/application.yaml

RUN mkdir -p examples/studies

COPY ./requirements.txt /conf/
COPY ./antarest /antarest
COPY ./resources /resources
COPY ./scripts /scripts
COPY ./alembic /alembic
COPY ./alembic.ini /alembic.ini

RUN ./scripts/install-debug.sh

RUN pip3 install --upgrade pip \
    && pip3 install -r /conf/requirements.txt


ENTRYPOINT ["./scripts/start.sh"]
