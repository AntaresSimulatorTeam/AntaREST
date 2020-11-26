#!/bin/bash

BASEDIR=$(dirname "$0")
PROJECT_DIR=$BASEDIR/..

cd "$PROJECT_DIR" || exit

source ./venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.

export API_ANTARES_STUDIES_PATH="$PROJECT_DIR"/examples/studies
export GUNICORN_CONFIG="$PROJECT_DIR"/conf/gunicorn.py

gunicorn --config "$GUNICORN_CONFIG" api_iso_antares.wsgi:app
