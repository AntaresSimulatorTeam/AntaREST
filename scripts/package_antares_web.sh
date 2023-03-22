#!/bin/bash

# Antares Web Packaging -- Desktop Version
#
# This script is launch by the GitHub Workflow `.github/workflows/deploy.yml`

set -e

ANTARES_SOLVER_VERSION="8.5"
ANTARES_SOLVER_FULL_VERSION="8.5.0"
ANTARES_SOLVER_FULL_VERSION_INT="850"

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd -P)
PROJECT_DIR=$(dirname -- "${SCRIPT_DIR}")
DIST_DIR="${PROJECT_DIR}/dist"
RESOURCES_DIR="${PROJECT_DIR}/resources"
ANTARES_SOLVER_DIR="${DIST_DIR}/AntaresWeb/antares_solver"

if [[ "$OSTYPE" == "msys"* ]]; then
  ANTARES_SOLVER_FOLDER_NAME="rte-antares-$ANTARES_SOLVER_FULL_VERSION-installer-64bits"
  ANTARES_SOLVER_ZIPFILE_NAME="$ANTARES_SOLVER_FOLDER_NAME.zip"
else
  ANTARES_SOLVER_ZIPFILE_NAME="antares-solver_ubuntu20.04.tar.gz"
fi

LINK="https://github.com/AntaresSimulatorTeam/Antares_Simulator/releases/download/v$ANTARES_SOLVER_FULL_VERSION/$ANTARES_SOLVER_ZIPFILE_NAME"

echo "INFO: Creating destination directory '${ANTARES_SOLVER_DIR}'..."
mkdir -p "${ANTARES_SOLVER_DIR}"

echo "INFO: Downloading '$ANTARES_SOLVER_ZIPFILE_NAME' in '$ANTARES_SOLVER_DIR'..."
cd "$ANTARES_SOLVER_DIR" || exit
wget $LINK

echo "INFO: Uncompressing '$ANTARES_SOLVER_ZIPFILE_NAME'..."
if [[ "$OSTYPE" == "msys"* ]]; then
  7z x $ANTARES_SOLVER_ZIPFILE_NAME
else
  tar xzf $ANTARES_SOLVER_ZIPFILE_NAME
fi
rm $ANTARES_SOLVER_ZIPFILE_NAME

if [[ "$OSTYPE" == "msys"* ]]; then
  echo "INFO: Moving executables in '$ANTARES_SOLVER_DIR'..."
  mv "$ANTARES_SOLVER_FOLDER_NAME/bin/antares-$ANTARES_SOLVER_VERSION-solver.exe" "$ANTARES_SOLVER_DIR"
  mv "$ANTARES_SOLVER_FOLDER_NAME/bin/sirius_solver.dll" "$ANTARES_SOLVER_DIR"
  mv "$ANTARES_SOLVER_FOLDER_NAME/bin/zlib1.dll" "$ANTARES_SOLVER_DIR"
  rm -rf $ANTARES_SOLVER_FOLDER_NAME
fi

echo "INFO: Copying basic configuration files..."
rm -rf "${DIST_DIR}/examples" # in case of replay
cp -r "${RESOURCES_DIR}"/deploy/* "${DIST_DIR}"
if [[ "$OSTYPE" == "msys"* ]]; then
  sed -i "s/700: path\/to\/700/$ANTARES_SOLVER_FULL_VERSION_INT: .\/AntaresWeb\/antares_solver\/antares-$ANTARES_SOLVER_VERSION-solver.exe/g" "${DIST_DIR}/config.yaml"
else
  sed -i "s/700: path\/to\/700/$ANTARES_SOLVER_FULL_VERSION_INT: .\/AntaresWeb\/antares_solver\/antares-$ANTARES_SOLVER_VERSION-solver/g" "${DIST_DIR}/config.yaml"
fi

echo "INFO: Creating shortcuts..."
if [[ "$OSTYPE" == "msys"* ]]; then
  cp "${RESOURCES_DIR}/AntaresWebServerShortcut.lnk" "${DIST_DIR}"
else
  # Create a relative link to `AntaresWebServer`
  cd "${DIST_DIR}"
  if [[ -f "AntaresWeb/AntaresWebServer" ]]; then
    ln -s "AntaresWeb/AntaresWebServer" "AntaresWebServer"
  else
    echo >&2 "WARNING: pyinstaller package 'AntaresWeb/AntaresWebServer' is missing"
  fi
fi

echo "INFO: Unzipping example study..."
cd "${DIST_DIR}/examples/studies" || exit
if [[ "$OSTYPE" == "msys"* ]]; then
  7z x example_study.zip
else
  unzip -q example_study.zip
fi
rm example_study.zip

echo "INFO: Antares Web Packaging DONE."
