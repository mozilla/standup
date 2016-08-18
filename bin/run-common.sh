#!/bin/bash -ex

# Migrate the db
python3 manage.py migrate --noinput
python3 manage.py collectstatic --noinput -c
