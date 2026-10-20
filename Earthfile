VERSION 0.8

tox:
    FROM python:3.15.0-alpine
    WORKDIR /app
    CACHE /root/.cache
    COPY requirements-tox.txt tox.ini .
    RUN python3 -m pip install --no-cache-dir -r requirements-tox.txt

    SAVE IMAGE --cache-hint

test:
    FROM +tox
    COPY --dir requirements-internal.txt.envtpl requirements-build.txt requirements-test.txt requirements.txt \
                MANIFEST.in README.md LICENSE.txt \
                setup.py odm_sdk \
                .

    # odm-api development builds are on TestPyPI, releases on PyPI
    ARG --required OPENAPI_VERSION
    RUN \
        python3 -m pip install --no-cache-dir envsubst && \
        cat requirements-internal.txt.envtpl | envsubst > requirements-internal.txt && \
        PIP_EXTRA_INDEX_URL=https://test.pypi.org/simple/ python3 -m tox run-parallel

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
    RUN python3 -m pip install --no-cache-dir -r requirements-build.txt

    # Releases go to PyPI, development builds to TestPyPI, and both to Nexus, which
    # functional-tests installs from
    ARG --required SDK_VERSION
    IF echo ${SDK_VERSION} | grep -Exq "^([0-9]+(.)?){3}$"
        ARG PYPI_REPOSITORY_INTERNAL="https://nexus.devops.gs.team/repository/pypi-releases/"
        ARG PYPI_REPOSITORY_PUBLIC="https://upload.pypi.org/legacy/"
        ARG PYPI_TOKEN_SECRET="PYPI_TOKEN"
    ELSE
        ARG PYPI_REPOSITORY_INTERNAL="https://nexus.devops.gs.team/repository/pypi-snapshots/"
        ARG PYPI_REPOSITORY_PUBLIC="https://test.pypi.org/legacy/"
        ARG PYPI_TOKEN_SECRET="PYPI_TOKEN_TEST"
    END

    # Push sdk
    RUN --push \
        --secret PYPI_TOKEN \
        --secret PYPI_TOKEN_TEST \
        --secret NEXUS_USER \
        --secret NEXUS_PASSWORD \
            TWINE_USERNAME="${NEXUS_USER}" TWINE_PASSWORD="${NEXUS_PASSWORD}" \
                twine upload dist/* --repository-url ${PYPI_REPOSITORY_INTERNAL} && \
            TWINE_USERNAME=__token__ TWINE_PASSWORD="pypi-$(printenv ${PYPI_TOKEN_SECRET})" \
                twine upload dist/* --repository-url ${PYPI_REPOSITORY_PUBLIC}

docs:
    FROM python:3.15.0
    WORKDIR /app

    # Build
    COPY --dir docs setup.py odm_sdk  .
    WORKDIR docs
    RUN \
        python3 -m pip install --no-cache-dir -r requirements.txt && \
        make markdown

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
    FROM sonarsource/sonar-scanner-cli:5.0.1
    ARG --required GIT_BRANCH_NAME
    COPY . .
    RUN \
        --secret SONAR_TOKEN \
            sonar-scanner \
                -Dsonar.branch.name=${GIT_BRANCH_NAME}

main:
    BUILD +push
    BUILD +docs
