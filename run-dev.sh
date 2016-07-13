#!/usr/bin/env bash
set -uex
docker run --net="host" -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -P griffon
