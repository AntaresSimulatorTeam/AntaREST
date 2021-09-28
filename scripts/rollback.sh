#!/bin/bash

CURDIR=$(cd `dirname $0` && pwd)
BASEDIR=`dirname $CURDIR`

cd $BASEDIR
alembic downgrade ab143a39c4db
cd -
