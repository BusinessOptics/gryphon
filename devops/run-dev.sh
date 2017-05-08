#!/usr/bin/env bash
set -eux
docker run \
	--net="host" \
	-e DEBUG=1 \
	-e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
	-e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
	-e AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION \
	-v "$(dirname "$(pwd)")":/web-server/ \
	-w /web-server/gryphon -i -t -P gryphon
