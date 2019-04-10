#!/bin/bash

PYTHON_TEMPLATES="src/main/python"
PROTOBUF_SOURCE="src/main/proto"

PYTHON_DIST="./dist"
PYTHON_DIST_DATA="${PYTHON_DIST}/data"

PYTHON_SOURCE="target/generated-sources/protobuf/python"
PYTHON_SOURCE_TARGET="${PYTHON_DIST}/openbase_type"

if [ ! -d $PYTHON_SOURCE ]; then
    # build source if not already done
    mvn package
fi

# copy python sources and meta
mkdir -p ${PYTHON_DIST_DATA}
mkdir -p ${PYTHON_SOURCE_TARGET}
cp -r ${PYTHON_SOURCE}/* ${PYTHON_SOURCE_TARGET}/
cp ${PYTHON_TEMPLATES}/* ${PYTHON_DIST}/
cp README.md ACKNOWLEDGMENT.md LICENSE.txt ${PYTHON_DIST}/

# copy raw protobuf types
cp -r ${PROTOBUF_SOURCE} ${PYTHON_DIST_DATA}/
