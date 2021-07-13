#!/bin/bash

CURDIR=$(cd `dirname $0` && pwd)
BASEDIR=`dirname $CURDIR`

pushd $BASEDIR
alembic downgrade 6a04e38b8704
popd
