#!/bin/bash

# Run from the host. This starts the db container if it's not running
# and figures out the container id. Then it runs pg_restore in the
# container piping standup.dump to it.

# Usage: restoredb.sh [FILENAME]

# Failures should exit
set -v -x

DC="$(which docker-compose)"
DOCKER="$(which docker)"
FILENAME="${1:-"standup.dump"}"

# Get the container id of the db container
cid="$(${DOCKER} ps --filter name=standup_db_1 --filter status=running -q)"

# If the db isn't started, start it up and then grab the container id
if [ "$cid" == "" ]; then
    ${DC} up -d db
    cid="$(${DOCKER} ps --filter name=standup_db_1 --filter status=running -q)"
fi

${DC} exec db dropdb -h localhost -U postgres -w postgres
${DC} exec db createdb -h localhost -U postgres -w postgres

cat ${FILENAME} | ${DOCKER} exec -i ${cid} pg_restore -d "postgres://postgres@localhost/postgres"

${DC} run app python manage.py migrate --fake-initial
${DC} run app python manage.py createsuperuser
