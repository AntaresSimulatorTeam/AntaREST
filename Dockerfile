FROM python:3.8-slim-buster

ENV ANTAREST_CONF /resources/application.yaml
ENV UVICORN_WORKERS 8
ENV UVICORN_ROOT_PATH /
ENV UVICORN_TIMEOUT 60

RUN mkdir -p examples/studies

COPY ./requirements.txt /conf/
COPY ./antarest /antarest
COPY ./resources /resources

RUN pip3 install --upgrade pip \
    && pip3 install -r /conf/requirements.txt

ENTRYPOINT uvicorn \
    --workers $UVICORN_WORKERS \
    --root-path $UVICORN_ROOT_PATH \
    --timeout-keep-alive $UVICORN_TIMEOUT \
    --host 0.0.0.0 \
    --port 5000 \
    antarest.wsgi:app