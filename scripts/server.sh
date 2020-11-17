#!/bin/bash

BASEDIR=$(dirname "$0")
PROJECT_DIR=$BASEDIR/..

cd "$PROJECT_DIR" || exit

source ./venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.
python ./api_iso_antares/main.py -j "$PROJECT_DIR"/examples/jsonschemas/STA-mini/jsonschema.json -s "$PROJECT_DIR"/examples/studies
