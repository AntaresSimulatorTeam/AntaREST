#!/bin/bash

CURDIR=$(cd `dirname $0` && pwd)
BASEDIR=`dirname $CURDIR`

cd $BASEDIR
alembic downgrade a845d5eae88e
cd -
