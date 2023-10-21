#!/bin/bash
# This script creates a new database migration.
#
# usage:
#
# export ANTAREST_CONF=/path/to/application.yaml
# bash ./scripts/scripts/create_db_migration.sh <name_of_your_migration>

set -e

CUR_DIR=$(cd "$(dirname "$0")" && pwd)
BASE_DIR=$(dirname "$CUR_DIR")


pushd "$BASE_DIR"

if [ -n "$1" ] ; then
  alembic revision --autogenerate -m "$1"
else
  alembic revision --autogenerate
fi

CURRENT_VERSION=$(alembic current)
sed -i "s/alembic downgrade .*/alembic downgrade $CURRENT_VERSION/g" "$CUR_DIR/rollback.sh"

popd
