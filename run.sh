#!/usr/bin/env bash
set -e

IMAGE_NAME=`docker build -q .`

docker run -it --rm --net=host -v /var/run/docker.sock:/var/run/docker.sock -v `pwd`/data:/do/data ${IMAGE_NAME}
