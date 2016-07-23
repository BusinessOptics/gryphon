#!/usr/bin/env bash
set -uex
if [ "$DEV_MODE" != 1 ];
then
    cd /web-server/ecs_view
	gunicorn -c gunicorn_config.py server:app -u root
else
	python3 /web-server/ecs_view/server.py
fi
