#!/bin/bash -e

# NOTE Do **not** set -x here as that would expose sensitive credentials
#      in the Travis build logs.

# tag has to be in the form "2016-08-30" (optionally with a ".1" after for same day deploys)
if [[ "$TRAVIS_TAG" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}(\.[0-9])?$ ]]; then
  HEROKU_APP="$HEROKU_PROD_APP"
  # TODO enable this when we're really ready for prod
  echo "Would have deployed to Prod on Heroku, but we're not ready yet."
  exit 0
elif [[ "$TRAVIS_BRANCH" == "master" ]]; then
  HEROKU_APP="$HEROKU_STAGE_APP"
else
  echo "Nothing to deploy"
  exit 0
fi

DOCKER_TAG="$DOCKER_REGISTRY/$HEROKU_APP/$HEROKU_PROC_TYPE"
docker login -e "$HEROKU_EMAIL" -u "$HEROKU_EMAIL" -p "$HEROKU_API_KEY" "$DOCKER_REGISTRY"
docker tag local/standup_base "$DOCKER_TAG"
docker push "$DOCKER_TAG"
