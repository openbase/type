#!/bin/bash

NC='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
ORANGE='\033[0;33m'
BLUE='\033[0;34m'
WHITE='\033[0;37m'

APP_NAME='type-cpp'
APP_NAME=${BLUE}${APP_NAME}${NC}
echo -e "=== ${APP_NAME} project ${WHITE}cleanup${NC}" &&
rm -rf build $@ &&
echo -e "=== ${APP_NAME} project ${WHITE}installation${NC}" &&
mkdir build
cd build
cmake ..
make -j 2 install
cd ..
echo -e "=== ${APP_NAME} was ${GREEN}successfully${NC} installed to ${WHITE}${prefix}${NC}"
