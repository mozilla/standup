DC = $(shell which docker-compose)
PG_DUMP_FILE ?= standup.dump
SERVER_URL ?= "http://web:8000"
HOSTUSER := $(shell id -u)

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

.env:
	@if [ ! -f .env ]; then \
		echo "Copying .env-dist to .env..."; \
		cp .env-dist .env; \
	fi

.docker-build:
	${MAKE} build

build: .env
	USERID=${HOSTUSER} ${DC} pull prod assets
	USERID=${HOSTUSER} ${DC} build prod
	USERID=${HOSTUSER} ${DC} build assets
	USERID=${HOSTUSER} ${DC} build app
	touch .docker-build

rebuild: clean .docker-build

run: .docker-build
	USERID=${HOSTUSER} ${DC} up assets app

shell: .docker-build
	USERID=${HOSTUSER} ${DC} run app python manage.py shell

restore-db: .docker-build
	./bin/restoredb.sh ${PG_DUMP_FILE}

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

	# static files
	-rm -rf static_build/
	-rm -rf staticfiles/

	# state files
	-rm -f .docker-build*

lint: .docker-build
	USERID=${HOSTUSER} ${DC} run test flake8 --statistics collector

test: .docker-build
	USERID=${HOSTUSER} ${DC} run test

test-image: .docker-build
	USERID=${HOSTUSER} ${DC} run test-image

test-smoketest: .docker-build
	USERID=${HOSTUSER} ${DC} run -e SERVER_URL=${SERVER_URL} test python tests/smoketest.py

docs: .docker-build
	USERID=${HOSTUSER} ${DC} run app $(MAKE) -C docs/ clean
	USERID=${HOSTUSER} ${DC} run app $(MAKE) -C docs/ html

.PHONY: default clean build docs lint run shell test test-image test-smoketest restore-db rebuild
