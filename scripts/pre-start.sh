#!/bin/bash
# Executes some setup tasks before the actual start of the web application:
# - database migration if needed
# - cleaning up lock files
# - fixing status of tasks that have been interrupted by previous shutdown
#
set -e

CUR_DIR=$(cd "$(dirname "$0")" && pwd)
BASE_DIR=$(dirname "$CUR_DIR")

cd "$BASE_DIR"
alembic upgrade head
cd -

export PYTHONPATH=$BASE_DIR
python3 "$BASE_DIR/antarest/tools/admin.py" clean-locks -c "$ANTAREST_CONF"
python3 "$BASE_DIR/antarest/tools/admin.py" fix-tasks-status -c "$ANTAREST_CONF"
