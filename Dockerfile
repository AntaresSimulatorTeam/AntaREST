FROM python:3.6-alpine3.8

ENV GUNICORN_WORKERS ALL_AVAILABLE
ENV ANTAREST_CONF /resources/application.yaml

RUN mkdir -p examples/studies

COPY ./requirements.txt ./conf/* /conf/
COPY ./antarest /antarest
COPY ./resources /resources

RUN pip3 install --upgrade pip \
    && pip3 install -r /conf/requirements.txt

ENTRYPOINT gunicorn --config /conf/gunicorn.py --worker-class=geventwebsocket.gunicorn.workers.GeventWebSocketWorker antarest.wsgi:app