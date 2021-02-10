#!/bin/bash

BASEDIR=$(dirname "$0")
PROJECT_DIR=$BASEDIR/..

cd "$PROJECT_DIR" || exit

source ./venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.

export ANTAREST_CONF="$PROJECT_DIR"/resources/application.yaml

GUNICORN_CONFIG="$PROJECT_DIR"/conf/gunicorn.py

gunicorn --config "$GUNICORN_CONFIG" antarest.wsgi:app
