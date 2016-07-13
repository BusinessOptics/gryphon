#!/usr/bin/env bash
set -uex
docker run --net="host" -e DEV_MODE=$DEV_MODE -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -v `pwd`:/web-server/ -w /web-server/ecs_view -i -t -P gryphon
