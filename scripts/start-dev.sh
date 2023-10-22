#!/bin/bash

set -e

BASE_DIR=$(dirname "$0")
PROJECT_DIR=$BASE_DIR/..

cd "$PROJECT_DIR"

source ./venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.

sh "$BASE_DIR/pre-start.sh"

python ./antarest/main.py -c ./resources/application.yaml
