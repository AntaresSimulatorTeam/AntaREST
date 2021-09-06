#!/bin/bash

CURDIR=$(cd `dirname $0` && pwd)
BASEDIR=`dirname $CURDIR`

cd $BASEDIR
alembic downgrade 897d56b780fe
cd -
