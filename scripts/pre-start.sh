#!/bin/bash

set -e

CUR_DIR=$(cd "$(dirname "$0")" && pwd)
BASE_DIR=$(dirname "$CUR_DIR")

cd "$BASE_DIR"
uv run alembic upgrade head
cd -

export PYTHONPATH=$BASE_DIR
uv run python "$BASE_DIR/antarest/tools/admin.py" clean-locks -c "$ANTAREST_CONF"
