FROM inca.rte-france.com/rtsi/python:3.6.5-centos7.4

ENV GUNICORN_WORKERS ALL_AVAILABLE
ENV API_ANTARES_STUDIES_PATH /studies

RUN mkdir $API_ANTARES_STUDIES_PATH

COPY ./requirements.txt ./conf/* /conf/
COPY ./antarest /antarest
COPY ./resources /resources

RUN pip3 install --upgrade pip \
    && pip3 install -r /conf/requirements.txt

ENTRYPOINT gunicorn --config /conf/gunicorn.py antarest.storage_api.wsgi:app