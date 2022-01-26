#!/bin/bash

set -e

CURDIR=$(cd `dirname $0` && pwd)
BASEDIR=`dirname $CURDIR`

if [ -z "$1" ] ; then
  sh $CURDIR/pre-start.sh
  gunicorn --config $BASEDIR/conf/gunicorn.py --worker-class=uvicorn.workers.UvicornWorker antarest.wsgi:app
else
  export PYTHONPATH=$BASEDIR
  python3 $BASEDIR/antarest/main.py -c $ANTAREST_CONF --module "$1"
fi