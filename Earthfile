VERSION 0.6

ARG --required DOCKER_REGISTRY_GROUP

build:
    FROM ${DOCKER_REGISTRY_GROUP}/genestack-builder:latest

    COPY . .

    RUN python3 setup.py sdist
    SAVE IMAGE --cache-hint

release:
    FROM +build

    RUN ./release.sh

