#!/bin/bash

ANTARES_SOLVER_VERSION="8.4"
ANTARES_SOLVER_FULL_VERSION="$ANTARES_SOLVER_VERSION.1"
ANTARES_SOLVER_FULL_VERSION_INT=$(echo $ANTARES_SOLVER_FULL_VERSION | sed 's/\.//g')

if [[ "$OSTYPE" == "msys"* ]]; then
  ANTARES_SOLVER_FOLDER_NAME="rte-antares-$ANTARES_SOLVER_FULL_VERSION-installer-64bits"
  ANTARES_SOLVER_ZIPFILE_NAME="$ANTARES_SOLVER_FOLDER_NAME.zip"
else
  ANTARES_SOLVER_FOLDER_NAME="antares-$ANTARES_SOLVER_FULL_VERSION-Ubuntu-20.04"
  ANTARES_SOLVER_ZIPFILE_NAME="$ANTARES_SOLVER_FOLDER_NAME.tar.gz"
fi

LINK="https://github.com/AntaresSimulatorTeam/Antares_Simulator/releases/download/v$ANTARES_SOLVER_FULL_VERSION/$ANTARES_SOLVER_ZIPFILE_NAME"
DESTINATION="../dist/AntaresWeb/antares_solver"

echo "Downloading AntaresSimulator from $LINK"
wget $LINK

echo "Unzipping $ANTARES_SOLVER_ZIPFILE_NAME and move Antares solver to $DESTINATION"
7z x $ANTARES_SOLVER_ZIPFILE_NAME
if [[ "$OSTYPE" != "msys"* ]]; then
  7z x "$ANTARES_SOLVER_FOLDER_NAME.tar"
fi

mkdir $DESTINATION

if [[ "$OSTYPE" == "msys"* ]]; then
  mv "$ANTARES_SOLVER_FOLDER_NAME/bin/antares-$ANTARES_SOLVER_VERSION-solver.exe" $DESTINATION
  mv $ANTARES_SOLVER_FOLDER_NAME/bin/sirius_solver.dll $DESTINATION
  mv $ANTARES_SOLVER_FOLDER_NAME/bin/zlib1.dll $DESTINATION
else
  mv "$ANTARES_SOLVER_FOLDER_NAME/bin/antares-$ANTARES_SOLVER_VERSION-solver" $DESTINATION
  mv "$ANTARES_SOLVER_FOLDER_NAME/bin/libsirius_solver.so" $DESTINATION
fi

echo "Copy basic configuration files"
cp -r ../resources/deploy/* ../dist/
if [[ "$OSTYPE" == "msys"* ]]; then
  sed -i "s/700: path\/to\/700/$ANTARES_SOLVER_FULL_VERSION_INT: .\/AntaresWeb\/antares_solver\/antares-$ANTARES_SOLVER_VERSION-solver.exe/g" ../dist/config.yaml
else
  sed -i "s/700: path\/to\/700/$ANTARES_SOLVER_FULL_VERSION_INT: .\/AntaresWeb\/antares_solver\/antares-$ANTARES_SOLVER_VERSION-solver/g" ../dist/config.yaml
fi

echo "Creating shortcuts"
if [[ "$OSTYPE" == "msys"* ]]; then
  cp ../resources/AntaresWebServerShortcut.lnk ../dist/
else
  ln -s ../dist/AntaresWeb/AntaresWebServer ../dist/AntaresWebServer
fi

echo "Unzipping example study"
cd ../dist/examples/studies
7z x example_study.zip
rm example_study.zip

echo "Cleaning up"
rm $ANTARES_SOLVER_ZIPFILE_NAME
rm -rf $ANTARES_SOLVER_FOLDER_NAME
