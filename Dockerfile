FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# RUN apt update && apt install -y procps gdb

# Add the `ls` alias to simplify debugging
RUN echo "alias ll='/bin/ls -l --color=auto'" >> /root/.bashrc

ENV ANTAREST_CONF /resources/application.yaml

RUN mkdir -p examples/studies

COPY ./pyproject.toml ./uv.lock /
COPY ./conf/* /conf/
COPY ./antarest /antarest
COPY ./resources /resources
COPY ./scripts /scripts
COPY ./alembic /alembic
COPY ./alembic.ini /alembic.ini

# Install dependencies using uv
RUN uv sync --frozen --no-dev

ENTRYPOINT ["./scripts/start.sh"]
