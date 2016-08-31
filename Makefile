DOCKERCOMPOSE = $(shell which docker-compose)

default:
	@echo "You need to specify a subcommand."
	make help
	@exit 1

help:
	@echo "build         - build docker containers for dev"
	@echo "run           - docker-compose up the entire system for dev"
	@echo ""
	@echo "clean         - remove all build, test, coverage and Python artifacts"
	@echo "lint          - check style with flake8"
	@echo "test          - run tests against local files"
	@echo "test-image    - run tests against files in docker image"
	@echo "test-coverage - run tests and generate coverage report in cover/"
	@echo "build-base    - (re)build base docker container"
	@echo "docs          - generate Sphinx HTML documentation, including API docs"

.docker-build-base:
	make build-base

.docker-build:
	make build

build-base:
	${DOCKERCOMPOSE} -f docker-compose.build.yml build --pull base
	-rm -f .docker-build
	touch .docker-build-base

build: .docker-build-base
	${DOCKERCOMPOSE} -f docker-compose.build.yml build web
	touch .docker-build

run: .docker-build
	${DOCKERCOMPOSE} up web

shell: .docker-build
	${DOCKERCOMPOSE} run web python3 manage.py shell

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

docs: .docker-build
	${DOCKERCOMPOSE} run web $(MAKE) -C docs/ clean
	${DOCKERCOMPOSE} run web $(MAKE) -C docs/ html

.PHONY: default clean build-base build docs lint run shell test test-coverage
