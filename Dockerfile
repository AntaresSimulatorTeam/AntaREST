FROM python:3.11-slim-bullseye

# RUN apt-get update && apt-get install -y procps gdb
RUN apt-get update && apt-get install -y --no-install-recommends p7zip-full \
    && rm -rf /var/lib/apt/lists/*

# Add the `ls` alias to simplify debugging
RUN echo "alias ll='/bin/ls -l --color=auto'" >> /root/.bashrc

ENV ANTAREST_CONF /resources/application.yaml

RUN mkdir -p examples/studies

COPY ./requirements.txt ./conf/* /conf/
COPY ./antarest /antarest
COPY ./resources /resources
COPY ./scripts /scripts
COPY ./alembic /alembic
COPY ./alembic.ini /alembic.ini

RUN pip3 install --no-cache-dir --upgrade pip && pip3 install --no-cache-dir -r /conf/requirements.txt

ENTRYPOINT ["./scripts/start.sh"]
