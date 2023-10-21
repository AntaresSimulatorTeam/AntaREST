#!/bin/bash
# This script downgrade the database version to the previous state.
#
# usage:
#
# export ANTAREST_CONF=/path/to/application.yaml
# bash ./scripts/scripts/rollback.sh

set -e

CUR_DIR=$(cd "$(dirname "$0")" && pwd)
BASE_DIR=$(dirname "$CUR_DIR")

cd "$BASE_DIR"
alembic downgrade 26c50ef2a0e1
cd -
