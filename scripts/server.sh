#!/bin/bash

BASEDIR=$(dirname "$0")
PROJECT_DIR=$BASEDIR/..

cd "$PROJECT_DIR" || exit

source ./venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.
python ./api_iso_antares/main.py -j /home/qdesmedt/Projects/rte/antares/api-iso-antares/examples/jsonschemas/STA-mini/jsonschema.json -s /home/qdesmedt/Projects/rte/antares/api-iso-antares/examples/studies
