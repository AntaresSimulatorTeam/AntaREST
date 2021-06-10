#!/bin/bash

CURDIR=$(cd `dirname $0` && pwd)
PROJECT_DIR=$CURDIR/../

SRC_FILE_LIST=(\
    "node_modules/jspreadsheet-ce/dist/jexcel.css" \
    "node_modules/jsuites/dist/jsuites.css" \
)

DEST_FILE_LIST=(
    "src/components/StudyView/StudyDataView/MatrixView/jexcel.css" \
    "src/components/StudyView/StudyDataView/MatrixView/jsuites.css" \
)

for i in ${!SRC_FILE_LIST[@]}; do
  ORIGIN=`md5sum $PROJECT_DIR${SRC_FILE_LIST[$i]} | cut -f 1 -d ' '`
  TARGET=`md5sum $PROJECT_DIR${DEST_FILE_LIST[$i]} | cut -f 1 -d ' '`
  if [ "$ORIGIN" != "$TARGET" ] ; then
    echo "${SRC_FILE_LIST[$i]} is different from ${DEST_FILE_LIST[$i]}"
    echo "Re-extract this lib file"
    exit 1;
  fi
done