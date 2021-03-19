ARG BASE_IMAGE=ubuntu:20.04

FROM ${BASE_IMAGE}

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends curl unzip ca-certificates less groff

WORKDIR /opt

ARG DOCKER_VERSION=20.10.5

RUN curl -Lo docker.tgz https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VERSION}.tgz && tar xvf docker.tgz --strip-component=1 docker/docker && mv docker /usr/local/bin && rm docker.tgz

RUN curl -Lo awscliv2.zip https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip && unzip awscliv2.zip && ./aws/install && rm -rf aws

ADD . .
