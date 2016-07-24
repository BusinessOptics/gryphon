#!/usr/bin/env bash
if [ "$DEBUG" != 1 ];
then
    cd /web-server/gryphon
    gunicorn -c gunicorn_config.py app:app -u root
else
    python3 /web-server/gryphon/app.py
fi
