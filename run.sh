#!/usr/bin/env bash
set -e

IMAGE_NAME=`docker build -q - < Dockerfile`

docker run -it --rm -v /var/run/docker.sock:/var/run/docker.sock -v `pwd`/cdk:/opt/cdk -v `pwd`/python:/opt/python ${IMAGE_NAME}
