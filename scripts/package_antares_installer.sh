#!/bin/bash

# Antares Desktop Installer
#
# This script must be run by  ̀.github/worflows/deploy.yml`.
# It builds the installer application and store it in the package directory.

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd -P)
PROJECT_DIR=$(dirname -- "${SCRIPT_DIR}")
INSTALLER_DIR="${PROJECT_DIR}/installer"
INSTALLER_SRC_DIR="${INSTALLER_DIR}/src/antares_web_installer"
DIST_DIR="${PROJECT_DIR}/dist/package"

echo "INFO: Initializing the virtual environment .installer"
if [[ "$OSTYPE" == "msys"* ]]; then
# initialize environment on windows
  python -m venv .installer
  .installer/bin/Activate.ps1
  python -m pip install -r ${INSTALLER_DIR}/requirements.txt
else
# initialize environment on linux
  python -m venv .installer
  source .installer/bin/activate
  python -m pip install -r ${INSTALLER_DIR}/requirements.txt
fi

# build package
echo "INFO: Generating the Installer for the Desktop application..."
if [[ "$OSTYPE" == "msys"* ]]; then
    pushd ${PROJECT_DIR}
    pyinstaller --onefile "${INSTALLER_SRC_DIR}/gui/__main__.py" --distpath "${DIST_DIR}" --hidden-import antares_web_installer.shortcuts._linux_shell --hidden-import antares_web_installer.shortcuts._win32_shell --noconsole --name AntaresWebInstaller
    popd
else
    pushd ${PROJECT_DIR}
    pyinstaller --onefile "${INSTALLER_SRC_DIR}/cli/__main__.py" --distpath "${DIST_DIR}" --hidden-import antares_web_installer.shortcuts._linux_shell --hidden-import antares_web_installer.shortcuts._win32_shell --noconsole --name AntaresWebInstallerCLI
    popd
fi

deactivate
rm -r .installer