#!/bin/bash -ex

export DATABASE_URL=sqlite://
export SECRET_KEY=itsasekrit
# export AUTH0_CLIENT_ID=foo
# export AUTH0_CLIENT_SECRET=foo
# export AUTH0_DOMAIN=foo
# export AUTH0_CALLBACK_URL=foo

flake8
py.test $@
