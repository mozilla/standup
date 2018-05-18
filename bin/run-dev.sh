#!/bin/bash -ex

urlwait
./bin/run-common.sh
exec python manage.py runserver 0.0.0.0:3000
