#!/bin/bash

# Antares Web Packaging -- Desktop Version
#
# This script is launch by the GitHub Workflow `.github/workflows/deploy.yml`.
# It builds the Desktop version of the Web Application.
# Make sure you run the `npm install` stage before running this script.

set -e

ANTARES_SOLVER_VERSION="8.8"
ANTARES_SOLVER_FULL_VERSION="8.8.14"
ANTARES_SOLVER_VERSION_INT="880"

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd -P)
PROJECT_DIR=$(dirname -- "${SCRIPT_DIR}")
DIST_DIR="${PROJECT_DIR}/dist/package"
RESOURCES_DIR="${PROJECT_DIR}/resources"
ANTARES_SOLVER_DIR="${DIST_DIR}/AntaresWeb/antares_solver"

if [[ "$OSTYPE" == "msys"* ]]; then
  ANTARES_SOLVER_FOLDER_NAME="antares-solver_windows"
  ANTARES_SOLVER_ZIPFILE_NAME="$ANTARES_SOLVER_FOLDER_NAME.zip"
else
  ANTARES_SOLVER_ZIPFILE_NAME="antares-solver_ubuntu20.04.tar.gz"
fi

LINK="https://github.com/AntaresSimulatorTeam/Antares_Simulator/releases/download/v$ANTARES_SOLVER_FULL_VERSION/$ANTARES_SOLVER_ZIPFILE_NAME"

echo "INFO: Preparing the Git Commit ID..."
git log -1 HEAD --format=%H > ${RESOURCES_DIR}/commit_id

echo "INFO: Remove the previous build if any..."
# Avoid the accumulation of files from previous builds (in development).
rm -rf ${DIST_DIR}

echo "INFO: Generating the Desktop version of the Web Application..."
if [[ "$OSTYPE" == "msys"* ]]; then
  pushd ${PROJECT_DIR}
  pyinstaller --distpath ${DIST_DIR} AntaresWebWin.spec
  popd
else
  pushd ${PROJECT_DIR}
  pyinstaller --distpath ${DIST_DIR} AntaresWebLinux.spec
  popd
fi

echo "INFO: Creating destination directory '${ANTARES_SOLVER_DIR}'..."
mkdir -p "${ANTARES_SOLVER_DIR}"

if [ -f "$ANTARES_SOLVER_ZIPFILE_NAME" ]; then
  echo "INFO: Using existing '$ANTARES_SOLVER_ZIPFILE_NAME' in '$ANTARES_SOLVER_DIR'..."
else
  echo "INFO: Downloading '$ANTARES_SOLVER_ZIPFILE_NAME' in '$ANTARES_SOLVER_DIR'..."
  cd "$ANTARES_SOLVER_DIR" || exit
  wget $LINK
fi

echo "INFO: Uncompressing '$ANTARES_SOLVER_ZIPFILE_NAME'..."
if [[ "$OSTYPE" == "msys"* ]]; then
  7z x $ANTARES_SOLVER_ZIPFILE_NAME
else
  tar xzf $ANTARES_SOLVER_ZIPFILE_NAME
fi
rm $ANTARES_SOLVER_ZIPFILE_NAME

if [[ "$OSTYPE" == "msys"* ]]; then
  echo "INFO: Moving executables in '$ANTARES_SOLVER_DIR'..."
  mv "$ANTARES_SOLVER_DIR/solver/Release/"* "$ANTARES_SOLVER_DIR"
  rm -rf $ANTARES_SOLVER_FOLDER_NAME
  rm -rf $"$ANTARES_SOLVER_DIR/solver/Release/"
fi

echo "INFO: Copying basic configuration files..."
rm -rf "${DIST_DIR}/examples" # in case of replay
cp -r "${RESOURCES_DIR}"/antares-desktop-fs/* "${DIST_DIR}"
if [[ "$OSTYPE" == "msys"* ]]; then
  sed -i "s/VER: ANTARES_SOLVER_PATH/$ANTARES_SOLVER_VERSION_INT: .\/AntaresWeb\/antares_solver\/antares-$ANTARES_SOLVER_VERSION-solver.exe/g" "${DIST_DIR}/config.yaml"
else
  sed -i "s/VER: ANTARES_SOLVER_PATH/$ANTARES_SOLVER_VERSION_INT: .\/AntaresWeb\/antares_solver\/antares-$ANTARES_SOLVER_VERSION-solver/g" "${DIST_DIR}/config.yaml"
fi

echo "INFO: Creating shortcuts..."
if [[ "$OSTYPE" == "msys"* ]]; then
  cp "${RESOURCES_DIR}/AntaresWebServerShortcut.lnk" "${DIST_DIR}"
else
  echo "INFO: Updating executable permissions..."
  chmod +x "${DIST_DIR}/AntaresWeb/AntaresWebServer"
fi

echo "INFO: Unzipping example study..."
# Basic study is located in the `deploy` directory
cp -r "${RESOURCES_DIR}/deploy/examples/studies/"* "${DIST_DIR}/studies"
cd "${DIST_DIR}/studies" || exit
if [[ "$OSTYPE" == "msys"* ]]; then
  7z x example_study.zip
else
  unzip -q example_study.zip
fi
rm example_study.zip

echo "INFO: Antares Web Packaging DONE."
