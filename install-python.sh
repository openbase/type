#!/bin/bash

NC='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
ORANGE='\033[0;33m'
BLUE='\033[0;34m'
WHITE='\033[0;37m'

APP_NAME='type-python'
APP_NAME=${BLUE}${APP_NAME}${NC}

PYTHON_DIST="./dist"

echo -e "=== ${APP_NAME} project ${WHITE}cleanup${NC}" &&
rm -rf ${PYTHON_DIST}
echo -e "=== ${APP_NAME} project ${WHITE}installation${NC}"

# prepare pythen dist
./prepare-python.sh

# change dir into python dist
cd ${PYTHON_DIST}

# generate package files
python3 package-gen.py

# generate source distribution
python3 setup.py sdist
python3 setup.py bdist_wheel

# install to default or given prefix
python3 setup.py install $@
echo -e "=== ${APP_NAME} was ${GREEN}successfully${NC} installed to ${WHITE}${prefix}${NC}"
