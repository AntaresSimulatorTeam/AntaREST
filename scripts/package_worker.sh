#!/bin/bash

# AntaresWebWorker packaging
#
# This script is launch by the GitHub Workflow `.github/workflows/worker.yml`.
# It builds the AntaresWebWorker.

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd -P)
PROJECT_DIR=$(dirname -- "${SCRIPT_DIR}")
DIST_DIR="${PROJECT_DIR}/dist"

echo "INFO: Generating the Worker Application..."
pushd ${PROJECT_DIR}
pyinstaller --distpath ${DIST_DIR} AntaresWebWorker.spec
popd

chmod +x "${DIST_DIR}/AntaresWebWorker"
