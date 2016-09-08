#!/bin/bash -ex

export DATABASE_URL=sqlite:// SECRET_KEY=itsasekrit

flake8
py.test $@
