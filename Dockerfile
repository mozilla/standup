##
# Static assets builder
#
FROM node:6-slim AS assets

ENV PATH=/app/node_modules/.bin:$PATH
WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install --pure-lockfile && rm -rf /usr/local/share/.cache/yarn
RUN npm install gulp-cli -g
COPY gulpfile.js ./
COPY ./static ./static
RUN gulp build --production

##
# Django app
#
FROM python:3.6-stretch AS webapp

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev postgresql-client build-essential gosu && \
    rm -rf /var/lib/apt/lists/*

# Extra python env
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Project settings
ENV DJANGO_SETTINGS_MODULE=standup.settings

EXPOSE 8000
WORKDIR /app
CMD ["./bin/run.sh", "prod"]

COPY requirements.txt ./
RUN pip install --require-hashes --no-cache-dir -r requirements.txt

COPY . /app
COPY --from=assets /app/static_build /app/static_build

# process static files
RUN bin/phb-manage.sh collectstatic --noinput -l

##
# Dev and test image
#
FROM webapp AS devapp

CMD ["./bin/run.sh", "dev"]

COPY requirements-dev.txt ./
RUN pip install --require-hashes --no-cache-dir -r requirements-dev.txt
