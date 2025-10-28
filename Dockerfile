FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# RUN apt update && apt install -y procps gdb

# Add the `ls` alias to simplify debugging
RUN echo "alias ll='/bin/ls -l --color=auto'" >> /root/.bashrc

ENV ANTAREST_CONF /resources/application.yaml

RUN mkdir -p examples/studies

COPY ./pyproject.toml ./uv.lock /app/
COPY ./conf/* /conf/
COPY ./antarest /app/antarest
COPY ./resources /resources
COPY ./scripts /scripts
COPY ./alembic /app/alembic
COPY ./alembic.ini /app/alembic.ini

WORKDIR /app

# Install dependencies using uv
RUN uv sync --frozen --no-dev

ENTRYPOINT ["./scripts/start.sh"]
