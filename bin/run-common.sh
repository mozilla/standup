#!/bin/bash -ex

# Migrate the db
# --fake-initial will fake the migration only if the table
# already exists. Needed for the initial migration in prod.
python manage.py migrate --noinput --fake-initial
