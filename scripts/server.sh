#!/bin/bash

BASEDIR=$(dirname "$0")
PROJECT_DIR=$BASEDIR/..

cd "$PROJECT_DIR" || exit

source ./venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.
python ./antarest/main.py -s "$PROJECT_DIR"/examples/studies
