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
ENV UV_HTTP_TIMEOUT=120
ENV UV_INDEX_URL=https://devin-depot.rte-france.com/repository/pypi-all/simple/
RUN uv venv /.venv && \
    uv export --frozen --no-dev --no-emit-project > /tmp/requirements.txt && \
    uv pip install -r /tmp/requirements.txt
ENV PATH="/.venv/bin:$PATH"

ENTRYPOINT ["./scripts/start.sh"]
