#!/bin/bash -ex

export SITE_URL=http://localhost:8000/
export DJANGO_SETTINGS_MODULE=standup.settings
export DATABASE_URL=sqlite://
export SECRET_KEY=itsasekrit
export STATICFILES_STORAGE=django.contrib.staticfiles.storage.StaticFilesStorage

export OIDC_RP_CLIENT_ID=ou812
export OIDC_RP_CLIENT_SECRET=secret_ou812
export OIDC_OP_DOMAIN=example.com

flake8
py.test $@
