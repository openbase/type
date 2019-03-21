#!/bin/bash

NC='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
ORANGE='\033[0;33m'
BLUE='\033[0;34m'
WHITE='\033[0;37m'

APP_NAME='type-python'
APP_NAME=${BLUE}${APP_NAME}${NC}


PYTHON_TEMPLATES="src/main/python"
PROTOBUF_SOURCE="src/main/proto"
PYTHON_SOURCE="target/generated-sources/protobuf/python/org/openbase/type"

PYTHON_DIST="./dist"
PYTHON_DIST_DATA="${PYTHON_DIST}/data"
PYTHON_DIST_SOURCE="${PYTHON_DIST}/openbase_type"

echo -e "=== ${APP_NAME} project ${WHITE}cleanup${NC}" &&
rm -rf ${PYTHON_DIST}
echo -e "=== ${APP_NAME} project ${WHITE}installation${NC}"

if [ ! -d $PYTHON_SOURCE ]; then
    # build source if not already done
    mvn package
fi

# copy python sources and meta
mkdir -p ${PYTHON_DIST_SOURCE}
mkdir -p ${PYTHON_DIST_DATA}
cp -r ${PYTHON_SOURCE}/* ${PYTHON_DIST_SOURCE}/
cp ${PYTHON_TEMPLATES}/* ${PYTHON_DIST}/
cp README.md ACKNOWLEDGMENT.md LICENSE.txt ${PYTHON_DIST}/

# copy raw protobuf types
cp -r ${PROTOBUF_SOURCE} ${PYTHON_DIST_DATA}/
cd ${PYTHON_DIST}

# generate package files
python package-gen.py

# generate source distribution
python setup.py sdist
python setup.py bdist_wheel
pip wheel -r requirements.txt

# install to default or given prefix
python setup.py install $@
echo -e "=== ${APP_NAME} was ${GREEN}successfully${NC} installed to ${WHITE}${prefix}${NC}"
