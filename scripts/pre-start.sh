#!/bin/bash

set -e

CURDIR=$(cd `dirname $0` && pwd)
BASEDIR=`dirname $CURDIR`

cd $BASEDIR
alembic upgrade head
cd -

export PYTHONPATH=$BASEDIR
python3 $BASEDIR/antarest/tools/admin.py clean_locks -c $ANTAREST_CONF