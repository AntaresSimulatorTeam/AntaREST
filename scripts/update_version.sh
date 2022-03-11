#!/bin/bash

CURDIR=$(cd `dirname $0` && pwd)
PROJECT_DIR=`dirname $CURDIR`

VERSION=$1

cd $PROJECT_DIR

sed -i "s/version=.*/version=\"$VERSION\",/g" setup.py
sed -i "s/sonar.projectVersion=.*/sonar.projectVersion=$VERSION/g" sonar-project.properties
sed -i "s/__version__ =.*/__version__ = \"$VERSION\"/g" antarest/__init__.py
sed -i "s/\"version\":.*/\"version\": \"$VERSION\",/g" webapp/package.json
sed -i "s/\"version\":.*/\"version\": \"$VERSION\",/g" webapp_v2/package.json