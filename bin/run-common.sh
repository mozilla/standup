#!/bin/bash

# Migrate the db
./manage.py migrate

# Collect any static files
./manage.py collectstatic --noinput -c
