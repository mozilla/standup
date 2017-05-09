#!/bin/bash -ex

export SERVER_MODE="${1:-dev}"
export LOG_LEVEL="${LOG_LEVEL:-info}"
exec "bin/run-${SERVER_MODE}.sh"
