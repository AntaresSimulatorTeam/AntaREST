#!/bin/bash

set -x

BASEDIR=$(dirname "$0")
PROJECT_DIR=$BASEDIR/..

cd "$PROJECT_DIR" || exit

docker build --tag antarest .

STUDIES_ABSOLUTE_PATH=$(realpath "$PROJECT_DIR"/examples/studies)

docker run \
  -p 80:5000 \
  -v "$STUDIES_ABSOLUTE_PATH":/studies \
  antarest