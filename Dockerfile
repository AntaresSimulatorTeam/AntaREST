FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# RUN apt-get update && apt-get install -y procps gdb
RUN apt-get update && apt-get install -y --no-install-recommends p7zip-full \
    && rm -rf /var/lib/apt/lists/*

# Add the `ls` alias to simplify debugging
RUN echo "alias ll='/bin/ls -l --color=auto'" >> /root/.bashrc

ENV ANTAREST_CONF=/resources/application.yaml

RUN mkdir -p examples/studies

# Install dependencies first (cached layer when only source code changes)
COPY ./pyproject.toml ./uv.lock ./LICENSE ./README.md /
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code and install the project itself
COPY ./antarest /antarest
COPY ./conf/* /conf/
COPY ./resources /resources
COPY ./scripts /scripts
COPY ./alembic /alembic
COPY ./alembic.ini /alembic.ini
RUN uv sync --frozen --no-dev

ENV PATH="/.venv/bin:$PATH"

ENTRYPOINT ["./scripts/start.sh"]
