#!/bin/bash -ex

export DJANGO_SETTINGS_MODULE=standup.settings
export DATABASE_URL=sqlite://
export SECRET_KEY=itsasekrit
export DJANGO_SETTINGS_MODULE=standup.settings
export STATICFILES_STORAGE=django.contrib.staticfiles.storage.StaticFilesStorage

export AUTH0_CLIENT_ID=ou812
export AUTH0_CLIENT_SECRET=ou812
export AUTH0_DOMAIN=foo

flake8
py.test $@
