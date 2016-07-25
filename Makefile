DOCKERCOMPOSE = $(shell which docker-compose)

default:
	@echo "You need to specify a subcommand."
	@exit 1

help:
	@echo "dev-like environment:"
	@echo "   build      - build docker containers for dev"
	@echo "   run        - docker-compose up the entire system for dev"
	@echo ""
	@echo "Mozilla prod-like environment:"
	@echo "   build-prod - build docker containers for prod"
	@echo "   run-prod   - docker-compose up the entire system for prod"
	@echo ""
	@echo "clean         - remove all build, test, coverage and Python artifacts"
	@echo "lint          - check style with flake8"
	@echo "test          - run tests"
	@echo "test-coverage - run tests and generate coverage report in cover/"
	@echo "docs          - generate Sphinx HTML documentation, including API docs"

# Prod configuration steps
.docker-build-prod:
	make build-prod

build-prod:
	${DOCKERCOMPOSE} -f docker-compose-prod.yml build
	touch .docker-build-prod

run-prod: .docker-build-prod
	${DOCKERCOMPOSE} -f docker-compose-prod.yml up

# Dev configuration steps
.docker-build:
	make build

build:
	${DOCKERCOMPOSE} build
	touch .docker-build

run: .docker-build
	${DOCKERCOMPOSE} up

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
	${DOCKERCOMPOSE} run appbase rm -rf cover

	# docs files
	-rm -rf docs/_build/

	# state files
	-rm .docker-build
	-rm .docker-build-prod

lint:
	${DOCKERCOMPOSE} run appbase flake8 --statistics collector

test:
	${DOCKERCOMPOSE} run appbase ./scripts/test.sh

test-coverage:
	${DOCKERCOMPOSE} run appbase ./scripts/test.sh --with-coverage --cover-package=collector --cover-inclusive --cover-html

docs:
	${DOCKERCOMPOSE} run appbase $(MAKE) -C docs/ clean
	${DOCKERCOMPOSE} run appbase $(MAKE) -C docs/ html
	${DOCKERCOMPOSE} run appbase find docs/_build/ -type d -exec 'chmod' '777' '{}' ';'
	${DOCKERCOMPOSE} run appbase find docs/_build/ -type f -exec 'chmod' '666' '{}' ';'

.PHONY: default clean build docs lint run test test-coverage
