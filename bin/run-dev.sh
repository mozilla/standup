#!/bin/bash -ex

urlwait
./bin/run-common.sh
exec python3 manage.py runserver 0.0.0.0:8000
