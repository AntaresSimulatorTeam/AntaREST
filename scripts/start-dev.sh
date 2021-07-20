#!/bin/bash

BASEDIR=$(dirname "$0")
PROJECT_DIR=$BASEDIR/..

cd "$PROJECT_DIR" || exit

source ./venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.

sh $BASEDIR/pre-start.sh

python ./antarest/main.py -c ./resources/application.yaml
