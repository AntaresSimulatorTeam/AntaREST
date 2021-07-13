#!/bin/bash

set -e

CURDIR=$(cd `dirname $0` && pwd)
BASEDIR=`dirname $CURDIR`

sh $CURDIR/pre_start.sh

gunicorn --config $BASEDIR/conf/gunicorn.py --worker-class=uvicorn.workers.UvicornWorker antarest.wsgi:app