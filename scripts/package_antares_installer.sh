#!/bin/bash

# Antares Desktop Installer
#
# This script must be run by  ̀.github/worflows/deploy.yml`.
# It builds the installer application and stores it in the package directory.

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd -P)
PROJECT_DIR=$(dirname -- "${SCRIPT_DIR}")
INSTALLER_DIR="${PROJECT_DIR}/installer"
DIST_DIR="${PROJECT_DIR}/dist/package"

# build package
echo "INFO: Generating the Installer..."

pushd ${INSTALLER_DIR}
if [[ "$OSTYPE" == "msys"* ]]; then
    # For windows we build the GUI version
    hatch run pyinstaller:build_cli AntaresWebInstaller
    mv dist/AntaresWebInstaller ${DIST_DIR}
else
    # For linux we build the command line version
    hatch run pyinstaller:build_cli AntaresWebInstallerCLI
    mv dist/AntaresWebInstallerCLI ${DIST_DIR}
fi
popd
