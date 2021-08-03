#!/bin/bash

CURDIR=$(cd `dirname $0` && pwd)
BASEDIR=`dirname $CURDIR`

cd $BASEDIR
alembic downgrade 15f3bce09264
cd -
