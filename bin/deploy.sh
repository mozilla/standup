#!/bin/bash -e

# NOTE Do **not** set -x here as that would expose sensitive credentials
#      in the Travis build logs.

# debugging info
echo "TRAVIS_TAG=$TRAVIS_TAG"
echo "TRAVIS_BRANCH=$TRAVIS_BRANCH"

# tag has to be in the form "2016-08-30" (optionally with a ".1" after for same day deploys)
if [[ "$1" == "prod" ]] && [[ "$TRAVIS_TAG" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}(\.[0-9])?$ ]]; then
  # TODO enable this when we're really ready for prod
  HEROKU_APP="$HEROKU_PROD_APP"
elif [[ "$1" == "stage" ]] && [[ "${TRAVIS_PULL_REQUEST}" == "false" ]] && [[ "$TRAVIS_BRANCH" == "master" ]]; then
  HEROKU_APP="$HEROKU_STAGE_APP"
else
  echo "Nothing to deploy"
  exit 0
fi

DOCKER_TAG="$DOCKER_REGISTRY/$HEROKU_APP/$HEROKU_PROC_TYPE"
echo "Pushing $DOCKER_TAG"
docker login -u "$HEROKU_EMAIL" -p "$HEROKU_API_KEY" "$DOCKER_REGISTRY"
docker tag mozmeao/standup:latest "$DOCKER_TAG"
docker push "$DOCKER_TAG"

# do Heroku release
DOCKER_IMAGE_ID=$(docker inspect "$DOCKER_TAG" --format={{.Id}})
curl -n -X PATCH https://api.heroku.com/apps/${HEROKU_APP}/formation \
  -d "{\"updates\": [{\"type\": \"web\", \"docker_image\": \"${DOCKER_IMAGE_ID}\"}]}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/vnd.heroku+json; version=3.docker-releases" \
  -H "Authorization: Bearer ${HEROKU_API_KEY}"

if [[ "$1" == "prod" && -n "$NEWRELIC_API_KEY" ]]; then
  curl -H "x-api-key:$NEWRELIC_API_KEY" \
       -d "deployment[app_name]=$NEWRELIC_APP_NAME" \
       -d "deployment[revision]=$TRAVIS_COMMIT" \
       -d "deployment[user]=Travis-CI" \
       https://api.newrelic.com/deployments.xml

  if [[ -n "$DOCKER_HUB_USER" ]]; then
    docker logout || true
    # push to docker hub for better cache for local dev and deployment
    docker login -u "$DOCKER_HUB_USER" -p "$DOCKER_HUB_PASS"
    docker push mozmeao/standup:latest
    docker tag mozmeao/standup:latest "mozmeao/standup:$TRAVIS_COMMIT"
    docker push "mozmeao/standup:$TRAVIS_COMMIT"
    docker push mozmeao/standup_assets:latest
    docker tag mozmeao/standup_assets:latest "mozmeao/standup_assets:$TRAVIS_COMMIT"
    docker push "mozmeao/standup_assets:$TRAVIS_COMMIT"
  fi
fi
