VERSION 0.6

ARG --required DOCKER_REGISTRY_GROUP
ARG --required RTD_TOKEN
ARG --required GITHUB_TOKEN
ARG --required GITHUB_USER
ARG --required GITHUB_USER_EMAIL

build:
    FROM ${DOCKER_REGISTRY_GROUP}/genestack-builder:latest

    COPY . .

    RUN python3 setup.py sdist
    SAVE IMAGE --cache-hint

release:
    FROM +build

    ### Get release version from version.py
    ARG RELEASE_VERSION=$(./setup.py --version)
    RUN echo "RELEASE_VERSION=${RELEASE_VERSION}"

    ### Check that RELEASE_VERSION exists in git tags.
    #ARG PRECONDITION=$(git tag -l | grep ${RELEASE_VERSION})
    #IF [ -z ${PRECONDITION} ]
    #    RUN echo "v${RELEASE_VERSION} wasn't found in git tags. Let's move on."
    #ELSE
    #    RUN echo "v${RELEASE_VERSION} was found in git tags. Stop script." && exit 1
    #END

    ### Check that RELEASE_VERSION exists in ChangeLog.
    ARG PRECONDITION=$(grep ${RELEASE_VERSION} ChangeLog)
    IF [ -z ${PRECONDITION} ]
        RUN echo "${RELEASE_VERSION} wasn't found in ChangeLog. Stop script." && exit 1
    ELSE
        RUN echo "${RELEASE_VERSION} was found in ChangeLog. Let's move on."
    END

    RUN --secret GITHUB_TOKEN \
     git config user.name ${GITHUB_USER} && \
     git config user.email ${GITHUB_USER_EMAIL} && \
     gh auth setup-git && \
     git fetch --all && \
     git checkout stable #&& \
     #git merge master && \
     #git push
     # echo ${GITHUB_TOKEN} > token.txt
     # gh auth login --with-token < mytoken.txt

    SAVE IMAGE --push docker-snapshots.devops.gs.team/tmp:123

    #RUN ./release.sh

