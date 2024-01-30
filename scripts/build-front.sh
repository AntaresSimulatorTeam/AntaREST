#!/bin/bash

set -e

CURR_DIR=$(cd "$(dirname "$0")" && pwd)

cd "$CURR_DIR"/../webapp

# When the web application is running in Desktop mode, 
# the web app is served at the `/static` entry point.
npm run build -- --base=/static/

cd ..
rm -fr resources/webapp
cp -r ./webapp/dist/ resources/webapp
cp ./webapp/dist/index.html resources/templates/
