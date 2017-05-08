#!/usr/bin/env bash
set -ex

nginx

if [ "$DEBUG" != 1 ];
then
    cd /web-server/gryphon
    gunicorn -c gunicorn_config.py app:app -u root
else
    python3.5 /web-server/gryphon/app.py
fi
