#!/bin/bash

# Antares Desktop Installer
#
# This script must be run by  ̀.github/worflows/deploy.yml`.
# It builds the installer application and store it in the package directory.

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd -P)
PROJECT_DIR=$(dirname -- "${SCRIPT_DIR}")
INSTALLER_DIR="${PROJECT_DIR}/installer/src/antares_web_installer/"
DIST_DIR="${PROJECT_DIR}/dist/package"

echo "INFO: Generating the Installer for the Desktop application..."
if [[ "$OSTYPE" == "msys"* ]]; then
    pushd ${PROJECT_DIR}
    pyinstaller --onefile "${INSTALLER_DIR}gui/__main__.py" --distpath "${DIST_DIR}" --hidden-import antares_web_installer.shortcuts._linux_shell --hidden-import antares_web_installer.shortcuts._win32_shell --noconsole --name AntaresWebInstaller
    popd
else
    pushd ${PROJECT_DIR}
    pyinstaller --onefile "${INSTALLER_DIR}cli/__main__.py" --distpath "${DIST_DIR}" --hidden-import antares_web_installer.shortcuts._linux_shell --hidden-import antares_web_installer.shortcuts._win32_shell --noconsole --name AntaresWebInstallerCLI
    popd
fi
