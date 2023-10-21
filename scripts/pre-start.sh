#!/bin/bash

set -e

CUR_DIR=$(cd "$(dirname "$0")" && pwd)
BASE_DIR=$(dirname "$CUR_DIR")

cd "$BASE_DIR"
alembic upgrade head
cd -

export PYTHONPATH=$BASE_DIR
python3 "$BASE_DIR/antarest/tools/admin.py" clean-locks -c "$ANTAREST_CONF"
