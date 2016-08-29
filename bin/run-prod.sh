#!/bin/bash -ex

./bin/run-common.sh
exec gunicorn standup.wsgi:application -b 0.0.0.0:${PORT:-8000} --log-file -
