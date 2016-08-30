#!/bin/bash -ex

export DATABASE_URL=sqlite:// SECRET_KEY=itsasekrit

py.test $@
