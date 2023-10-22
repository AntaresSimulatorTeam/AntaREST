#!/bin/bash

set -e

CUR_DIR=$(cd "$(dirname "$0")" && pwd)
BASE_DIR=$(dirname "$CUR_DIR")

if [ -z "$1" ] ; then
  sh $CUR_DIR/pre-start.sh
  gunicorn --config $BASE_DIR/conf/gunicorn.py --worker-class=uvicorn.workers.UvicornWorker antarest.wsgi:app
else
  export PYTHONPATH=$BASE_DIR
  python3 $BASE_DIR/antarest/main.py -c $ANTAREST_CONF --module "$1"
fi