#!/usr/bin/env bash
set -ex
if [ "$DEV_MODE" != 1 ];
then
	gunicorn -c gunicorn_config.py server:app -u root
else
	python3 server.py
fi
