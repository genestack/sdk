VERSION 0.8

tox:
    FROM python:3.12.4-alpine
    DO github.com/genestack/earthly-libs+PYTHON_PREPARE
    CACHE /root/.cache
    COPY requirements-tox.txt tox.ini .
    RUN \
        --secret NEXUS_USER \
        --secret NEXUS_PASSWORD \
            pypi-login.sh && \
            python3 -m pip install --no-cache-dir -r requirements-tox.txt && \
            pypi-clean.sh

    SAVE IMAGE --cache-hint

test:
    FROM +tox
    COPY --dir requirements-internal.txt.envtpl requirements-build.txt requirements-test.txt requirements.txt \
                MANIFEST.in README.md LICENSE.txt \
                setup.py odm_sdk \
                .

    ARG --required OPENAPI_VERSION
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
        python3 -m pip install --no-cache-dir envsubst && \
        cat odm_sdk/version.py.envtpl | envsubst > odm_sdk/version.py && \
        python3 setup.py sdist

    SAVE IMAGE --cache-hint

push:
    FROM +build
    RUN \
        --secret NEXUS_USER \
        --secret NEXUS_PASSWORD \
            pypi-login.sh && \
            python3 -m pip install --no-cache-dir -r requirements-build.txt && \
            pypi-clean.sh

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

docs:
    FROM python:3.12.4
    DO github.com/genestack/earthly-libs+PYTHON_PREPARE

    # Build
    COPY --dir docs setup.py odm_sdk  .
    WORKDIR docs
    RUN \
        --secret NEXUS_USER \
        --secret NEXUS_PASSWORD \
            pypi-login.sh && \
            python3 -m pip install --no-cache-dir -r requirements.txt && \
            make markdown && \
            pypi-clean.sh

    # Push
    WORKDIR build/markdown
    ARG --required RAW_REGISTRY_SNAPSHOTS
    ARG --required SDK_VERSION
    RUN \
        --push \
        --secret NEXUS_USER \
        --secret NEXUS_PASSWORD \
            export DOC_ARCHIVE=odm-sdk-${SDK_VERSION}.tar.gz && \
            tar cf ${DOC_ARCHIVE} * && \
            curl -v --fail --user ${NEXUS_USER}:${NEXUS_PASSWORD} \
                -H 'Content-Type: application/gzip' \
                 --upload-file ${DOC_ARCHIVE} \
                 ${RAW_REGISTRY_SNAPSHOTS}/docs/odm-sdk/${DOC_ARCHIVE}

sonarcloud:
    FROM sonarsource/sonar-scanner-cli:10.0.0
    DO --pass-args github.com/genestack/earthly-libs+SONARCLOUD_RUN

main:
    BUILD +push
    BUILD +docs
