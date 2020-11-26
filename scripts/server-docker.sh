#!/bin/bash

set -x

BASEDIR=$(dirname "$0")
PROJECT_DIR=$BASEDIR/..

cd "$PROJECT_DIR" || exit

docker build --tag api-iso-antares -f docker/Dockerfile .

STUDIES_ABSOLUTE_PATH=$(realpath "$PROJECT_DIR"/examples/studies)

docker run \
  -p 80:5000 \
  -e GUNICORN_WORKERS=ALL_AVAILABLE \
  -v "$STUDIES_ABSOLUTE_PATH":/studies \
  api-iso-antares