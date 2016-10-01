#!/bin/bash -ex

./bin/run-common.sh
exec newrelic-admin run-program gunicorn standup.wsgi:application -b 0.0.0.0:${PORT:-8000} \
                                         --log-file - \
                                         --max-requests ${MAX_REQUESTS:-10000} \
                                         --max-requests-jitter ${MAX_REQUESTS_JITTER:-500}
