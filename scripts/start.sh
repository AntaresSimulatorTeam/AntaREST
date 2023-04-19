#!/bin/bash

set -e

CURDIR=$(cd `dirname $0` && pwd)
BASEDIR=`dirname $CURDIR`

if [[ -v PROMETHEUS_MULTIPROC_DIR ]]; then
  rm ${PROMETHEUS_MULTIPROC_DIR}/*.db
  mkdir -p ${PROMETHEUS_MULTIPROC_DIR}
  echo "Concatenating metrics into ${PROMETHEUS_MULTIPROC_DIR}"
fi

if [ -z "$1" ] ; then
  sh $CURDIR/pre-start.sh
  gunicorn --config $BASEDIR/conf/gunicorn.py --worker-class=uvicorn.workers.UvicornWorker antarest.wsgi:app
else
  export PYTHONPATH=$BASEDIR
  python3 $BASEDIR/antarest/main.py -c $ANTAREST_CONF --module "$1"
fi