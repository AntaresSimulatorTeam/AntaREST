#!/bin/bash

CURDIR=$(cd `dirname $0` && pwd)
BASEDIR=`dirname $CURDIR`

pushd $BASEDIR
alembic upgrade head
popd