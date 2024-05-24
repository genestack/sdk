VERSION 0.8

ARG --global --required HARBOR_DOCKER_REGISTRY
ARG --global --required PYPI_REGISTRY_GROUP
ARG --global --required PYPI_REGISTRY_RELEASES
ARG --global --required PYPI_REGISTRY_SNAPSHOTS
ARG --global --required PYPI_REGISTRY_PYPI_ORG_MIRROR
ARG --global --required NEXUS_URL

sonarcloud:
    FROM sonarsource/sonar-scanner-cli:5.0.1
    ARG --required GIT_BRANCH_NAME
    COPY . .
    RUN \
        --secret SONAR_TOKEN \
            sonar-scanner \
                -Dsonar.branch.name=${GIT_BRANCH_NAME}

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
        ARG PYPI_REPOSITORY_INTERNAL="nexus-pypi-releases"
        ARG PYPI_REPOSITORY_PUBLIC="pypi"
    ELSE
        ARG PYPI_REPOSITORY_INTERNAL="nexus-pypi-snapshots"
        ARG PYPI_REPOSITORY_PUBLIC="testpypi"
    END

    # Push sdk
    RUN --push \
        --secret PYPI_TOKEN \
        --secret PYPI_TOKEN_TEST \
        --secret NEXUS_USER \
        --secret NEXUS_PASSWORD \
            pypi-login.sh && \
            twine upload dist/* -r ${PYPI_REPOSITORY_INTERNAL} && \
            twine upload dist/* -r ${PYPI_REPOSITORY_PUBLIC} && \
            pypi-clean.sh

rtd:
    FROM +build

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
