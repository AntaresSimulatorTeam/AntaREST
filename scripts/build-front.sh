#!/bin/bash

CURDIR=$(cd `dirname $0` && pwd)

cd $CURDIR/../webapp

sed -i 's|"homepage".*|"homepage": "./static",|g' package.json
sed -i 's|loadPath.*|loadPath: "/static/locales/{{lng}}/{{ns}}.json",|g' src/i18n.js

npm run build

sed -i 's|"homepage".*|"homepage": "./",|g' package.json
sed -i 's|loadPath.*|loadPath: "./locales/{{lng}}/{{ns}}.json",|g' src/i18n.js

cd ..
rm -fr resources/webapp
cp -r ./webapp/build/ resources/webapp
