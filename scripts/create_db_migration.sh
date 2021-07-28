#!/bin/bash

CURDIR=$(cd `dirname $0` && pwd)
BASEDIR=`dirname $CURDIR`


pushd $BASEDIR

if [ -n "$1" ] ; then
  alembic revision --autogenerate -m "$1"
else
  alembic revision --autogenerate
fi

CURRENT_VERSION=$(alembic current)
sed -i "s/alembic downgrade .*/alembic downgrade $CURRENT_VERSION/g" $CURDIR/rollback.sh

popd