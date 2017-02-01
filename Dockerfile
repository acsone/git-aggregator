FROM python:3-alpine
MAINTAINER Tecnativa <info@tecnativa.com>
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
ENV GIT_AUTHOR_NAME=git-aggregator \
    EMAIL=https://hub.docker.com/r/tecnativa/git-aggregator
# HACK Install git >= 2.11, to have --shallow-since
# TODO Remove HACK when python:alpine is alpine >= v3.5
RUN apk add --no-cache --repository http://dl-cdn.alpinelinux.org/alpine/v3.5/main git
COPY . /usr/src/app
RUN pip install --no-cache-dir --editable /usr/src/app
RUN python -m compileall /usr/src/app/
VOLUME /repos
WORKDIR /repos
