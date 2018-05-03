#!/bin/bash -ex

export SERVER_MODE="${1:-dev}"
export LOG_LEVEL="${LOG_LEVEL:-info}"
# add non-priviledged user
USERID="${USERID:-0}"
if [[ "$USERID" == "0" ]]; then
    exec "bin/run-${SERVER_MODE}.sh"
else
    adduser --uid "$USERID" --disabled-password --gecos '' --no-create-home webdev
    gosu webdev "bin/run-${SERVER_MODE}.sh"
fi
