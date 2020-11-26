FROM python:3.6-alpine3.8

ENV GUNICORN_WORKERS ALL_AVAILABLE
ENV API_ANTARES_STUDIES_PATH /studies

RUN mkdir $API_ANTARES_STUDIES_PATH

COPY ./requirements.txt ./conf/* /conf/
COPY ./api_iso_antares /api_iso_antares
COPY ./resources /resources

RUN pip install --upgrade pip && pip install -r /conf/requirements.txt

ENTRYPOINT gunicorn --config /conf/gunicorn.py api_iso_antares.wsgi:app