#!/bin/bash

set -e

CURDIR=$(cd `dirname $0` && pwd)

cd $CURDIR/../webapp

if [[ "$OSTYPE" == "darwin"* ]]; then
sed -i '' 's|"homepage".*|"homepage": "/static",|g' package.json
sed -i '' 's|loadPath.*|loadPath: `/static/locales/{{lng}}/{{ns}}.json?v=${version}`,|g' src/i18n.js
else
sed -i 's|"homepage".*|"homepage": "/static",|g' package.json
sed -i 's|loadPath.*|loadPath: `/static/locales/{{lng}}/{{ns}}.json?v=${version}`,|g' src/i18n.js
fi

./node_modules/.bin/cross-env GENERATE_SOURCEMAP=false npm run build

if [[ "$OSTYPE" == "darwin"* ]]; then
sed -i '' 's|"homepage".*|"homepage": "/",|g' package.json
sed -i '' 's|loadPath.*|loadPath: `/locales/{{lng}}/{{ns}}.json?v=${version}`,|g' src/i18n.js
else
sed -i 's|"homepage".*|"homepage": "/",|g' package.json
sed -i 's|loadPath.*|loadPath: `/locales/{{lng}}/{{ns}}.json?v=${version}`,|g' src/i18n.js
fi

cd ..
rm -fr resources/webapp
cp -r ./webapp/build/ resources/webapp
cp ./webapp/build/index.html resources/templates/
