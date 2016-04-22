#!/bin/bash

RED='\033[0;31m'
NONE='\033[0m'

DIR_1="$1"
DIR_2="$2"

TYPES_1="$(find "$DIR_1" -type f -name "*proto" | sed "s%${DIR_1}/proto/.*/rst/%%" | sort)"
TYPES_2="$(find "$DIR_2" -type f -name "*proto" | sed "s%${DIR_2}/proto/.*/rst/%%" | sort)"

AMBIGUITIES="$(join <(echo "$TYPES_1") <(echo "$TYPES_2"))"

if [ "$AMBIGUITIES" != "" ]; then
  NICER="$(echo "$AMBIGUITIES" | sed "s%^%\t\\\033[0;31m%" | sed "s%$%\\\033[0m%")"
  echo -e "Ambiguous prototypes found. Already existing:\n$NICER"
  exit 1
else
  echo -e "No Ambiguities found."
  exit 0
fi
