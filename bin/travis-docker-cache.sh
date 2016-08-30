#!/bin/bash -ex

case "$1" in
  save)
    # Save built images to Travis cache directory
    if [[ "${TRAVIS_PULL_REQUEST}" == "false" ]] && [[ "${TRAVIS_BRANCH}" == "master" ]]; then
      mkdir -p $(dirname "${DOCKER_CACHE_FILE}")
      docker save $(docker history -q local/standup_dev | grep -v '<missing>') | \
             gzip > "${DOCKER_CACHE_FILE}"
    fi
    ;;
  load)
    if [[ -f "${DOCKER_CACHE_FILE}" ]]; then
      gunzip -c "${DOCKER_CACHE_FILE}" | docker load
    fi
    ;;
  *)
    echo "Unknown action $1"
esac
