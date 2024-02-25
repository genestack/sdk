VERSION 0.8

ARG --global --required HARBOR_DOCKER_REGISTRY
ARG --global --required PYPI_REGISTRY_GROUP
ARG --global --required PYPI_REGISTRY_RELEASES
ARG --global --required PYPI_REGISTRY_SNAPSHOTS
ARG --global --required PYPI_REGISTRY_PYPI_ORG_MIRROR
ARG --global --required NEXUS_URL

tox:
    ARG --required BASE_IMAGES_VERSION
    FROM ${HARBOR_DOCKER_REGISTRY}/builder:${BASE_IMAGES_VERSION}
    COPY requirements-tox.txt tox.ini .
    RUN \
        --secret NEXUS_USER \
        --secret NEXUS_PASSWORD \
            pypi-login.sh && \
            python3 -m pip install --no-cache-dir -r requirements-tox.txt && \
            pypi-clean.sh

    SAVE IMAGE --cache-hint

test:
    ARG --required OPENAPI_VERSION
    FROM +tox
    COPY --dir requirements-internal.txt.envtpl requirements-build.txt requirements-test.txt requirements.txt \
                MANIFEST.in README.md LICENSE.txt \
                setup.py odm_sdk \
                .
    RUN \
        --secret NEXUS_USER \
        --secret NEXUS_PASSWORD \
            pypi-login.sh && \
            cat requirements-internal.txt.envtpl | envsubst > requirements-internal.txt && \
            python3 -m tox run-parallel && \
            pypi-clean.sh

    SAVE IMAGE --cache-hint

build:
    FROM +test
    ARG --required SDK_VERSION
    RUN \
        cat odm_sdk/version.py.envtpl | envsubst > odm_sdk/version.py && \
        python3 setup.py sdist

    SAVE IMAGE --cache-hint

push:
    FROM +build

    RUN python3 -m pip install --no-cache-dir -r requirements-build.txt

    ARG --required SDK_VERSION
    IF echo ${SDK_VERSION} | grep -Exq "^([0-9]+(.)?){3}$"
        ARG PYPI_REPOSITORY_FIRST="nexus-pypi-releases"
        ARG PYPI_REPOSITORY_SECOND="pypi"
    ELSE
        ARG PYPI_REPOSITORY_FIRST="nexus-pypi-snapshots"
        ARG PYPI_REPOSITORY_SECOND="testpypi"
    END

    # Push sdk
    RUN --push \
        --secret PYPI_TOKEN \
        --secret PYPI_TOKEN_TEST \
        --secret NEXUS_USER \
        --secret NEXUS_PASSWORD \
            pypi-login.sh && \
            twine upload dist/* -r ${PYPI_REPOSITORY_FIRST} && \
            twine upload dist/* ${PYPI_REPOSITORY_SECOND} && \
            pypi-clean.sh

public:
    FROM +build

    ### Get release version from version.py
    ARG RELEASE_VERSION=$(./setup.py --version)
    RUN echo --no-cache "RELEASE_VERSION=${RELEASE_VERSION}"

    ## Check that RELEASE_VERSION exists in git tags.
    ARG GIT_TAG_PRECONDITION=$(git tag -l | grep ${RELEASE_VERSION})
    IF [ -z ${GIT_TAG_PRECONDITION} ]
        RUN --no-cache echo "v${RELEASE_VERSION} wasn't found in git tags. Let's move on."
    ELSE
        RUN --no-cache echo "v${RELEASE_VERSION} was found in git tags. Stop script." && exit 1
    END

    ### Check that RELEASE_VERSION exists in ChangeLog.
    ARG CHANGE_LOG_PRECONDITION=$(grep ${RELEASE_VERSION} ChangeLog)
    IF [ -z ${CHANGE_LOG_PRECONDITION} ]
        RUN --no-cache echo "${RELEASE_VERSION} wasn't found in ChangeLog. Stop script." && exit 1
    ELSE
        RUN --no-cache echo "${RELEASE_VERSION} was found in ChangeLog. Let's move on."
    END

    # Git magic (merge master to stable and push tag)
    RUN --push \
        --secret GITHUB_TOKEN \
        --secret GITHUB_USER \
        --secret GITHUB_USER_EMAIL \
            git config user.name ${GITHUB_USER} && \
            git config user.email ${GITHUB_USER_EMAIL} && \
            gh auth setup-git && \
            git fetch --all && \
            git checkout stable && \
            git merge master && \
            git checkout master && \
            git push && \
            git tag -l | xargs git tag -d && \
            git fetch --tags && \
            git tag v${RELEASE_VERSION} && \
            git push --tags

    ## Create Github release
    RUN --push \
        --secret GITHUB_TOKEN \
        --secret GITHUB_USER \
        --secret GITHUB_USER_EMAIL \
            curl \
                -X POST \
                -H "Accept: application/vnd.github+json" \
                -H "Authorization: Bearer ${GITHUB_TOKEN}" \
                -H "X-GitHub-Api-Version: 2022-11-28" \
                "https://api.github.com/repos/genestack/python-client/releases" \
                -d '{"tag_name":"v'${RELEASE_VERSION}'","target_commitish":"master","name":"genestack-python-client-v'${RELEASE_VERSION}'","body":"Description of the release here: https://github.com/genestack/python-client/blob/v'${RELEASE_VERSION}'/ChangeLog","draft":false,"prerelease":false,"generate_release_notes":false}'

    ## Trigger Read the docs builds
    RUN --push \
        --secret RTD_TOKEN \
            curl \
            -X POST \
            -H "Authorization: Token ${RTD_TOKEN}" "https://readthedocs.org/api/v3/projects/genestack-client/versions/latest/builds/" && \
            curl \
            -X POST \
            -H "Authorization: Token ${RTD_TOKEN}" "https://readthedocs.org/api/v3/projects/genestack-client/versions/stable/builds/"

main:
    BUILD +push
