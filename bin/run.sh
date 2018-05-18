#!/bin/bash -ex

export SERVER_MODE="${1:-dev}"
export LOG_LEVEL="${LOG_LEVEL:-info}"
# add non-priviledged user
USERID="${USERID:-0}"
if [[ "$USERID" == "0" ]]; then
    exec "bin/run-${SERVER_MODE}.sh"
else
    if ! id webdev >/dev/null 2>&1; then
        adduser --uid "$USERID" --disabled-password --gecos '' --no-create-home webdev
    fi
    gosu webdev "bin/run-${SERVER_MODE}.sh"
fi
