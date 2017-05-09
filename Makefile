DOCKERCOMPOSE = $(shell which docker-compose)
PG_DUMP_FILE ?= standup.dump
SERVER_URL ?= "http://web:8000"

default: help
	@echo ""
	@echo "You need to specify a subcommand."
	@exit 1

help:
	@echo "build         - build docker images for dev"
	@echo "run           - docker-compose up the entire system for dev"
	@echo ""
	@echo "clean         - remove all build, test, coverage and Python artifacts"
	@echo "rebuild       - force a rebuild of all of the docker images"
	@echo "lint          - check style with flake8"
	@echo "test          - run tests against local files"
	@echo "test-image    - run tests against files in docker image"
	@echo "test-smoketest- run smoke tests against SERVER_URL"
	@echo "build-base    - (re)build base docker image"
	@echo "docs          - generate Sphinx HTML documentation, including API docs"

.docker-build-base:
	${MAKE} build-base

.docker-build:
	${MAKE} build

build-base:
	${DOCKERCOMPOSE} -f docker-compose.build.yml build --pull base
	-rm -f .docker-build
	touch .docker-build-base

build: .docker-build-base
	${DOCKERCOMPOSE} -f docker-compose.build.yml build web
	touch .docker-build

rebuild: clean .docker-build

run: .docker-build
	${DOCKERCOMPOSE} up web

shell: .docker-build
	${DOCKERCOMPOSE} run web python manage.py shell

restore-db: .docker-build
	-${DOCKERCOMPOSE} run web dropdb -h db -U postgres -w postgres
	${DOCKERCOMPOSE} run web createdb -h db -U postgres -w postgres
	-${DOCKERCOMPOSE} run web pg_restore -d "postgres://postgres@db/postgres" < ${PG_DUMP_FILE}
	${DOCKERCOMPOSE} run web python manage.py migrate --fake-initial
	${DOCKERCOMPOSE} run web python manage.py createsuperuser

clean:
	# python related things
	-rm -rf build/
	-rm -rf dist/
	-rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

	# test related things
	-rm -f .coverage

	# docs files
	-rm -rf docs/_build/

	# state files
	-rm -f .docker-build*

lint: .docker-build
	${DOCKERCOMPOSE} run web flake8 --statistics collector

test: .docker-build
	${DOCKERCOMPOSE} run test

test-image: .docker-build
	${DOCKERCOMPOSE} run test-image

test-smoketest: .docker-build
	${DOCKERCOMPOSE} run -e SERVER_URL=${SERVER_URL} test python tests/smoketest.py

docs: .docker-build
	${DOCKERCOMPOSE} run web $(MAKE) -C docs/ clean
	${DOCKERCOMPOSE} run web $(MAKE) -C docs/ html

.PHONY: default clean build-base build docs lint run shell test test-image test-smoketest restore-db rebuild
