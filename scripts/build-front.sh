#!/bin/bash

set -e

CURR_DIR=$(cd "$(dirname "$0")" && pwd)

cd "$CURR_DIR"/../webapp
npm run build
cd ..
rm -fr resources/webapp
cp -r ./webapp/dist/ resources/webapp
cp ./webapp/dist/index.html resources/templates/
