#!/bin/bash -ex

export DJANGO_SETTINGS_MODULE=standup.settings
export DATABASE_URL=sqlite://
export SECRET_KEY=itsasekrit

export OIDC_RP_CLIENT_ID=ou812
export OIDC_RP_CLIENT_SECRET=secret_ou812
export OIDC_OP_DOMAIN=example.com

flake8
py.test $@
