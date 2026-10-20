VERSION 0.8

tox:
    FROM astral/uv:0.13.1-python3.15-alpine
    WORKDIR /app
    CACHE /root/.cache
    COPY requirements-tox.txt tox.ini .
    RUN uv pip install --system --no-cache -r requirements-tox.txt

    SAVE IMAGE --cache-hint

test:
    FROM +tox
    COPY --dir requirements-internal.txt.envtpl requirements-build.txt requirements-test.txt requirements.txt \
                uv.toml MANIFEST.in README.md LICENSE.txt \
                setup.py odm_sdk \
                .

    # odm-api development builds are on TestPyPI, releases on PyPI. tox-uv installs with the
    # image's uv, which uv.toml lets fall back to TestPyPI only for what PyPI lacks.
    # TestPyPI's CDN can serve an index without a new version for up to 10 minutes after its
    # upload (Cache-Control: max-age=600), so odm-api is resolved first, retried until the
    # index lists it; tox's uv then reads that page from the same cache.
    ARG --required OPENAPI_VERSION
    RUN \
        cat requirements-internal.txt.envtpl | uvx --no-cache envsubst > requirements-internal.txt && \
        for i in $(seq 60); do \
            uv pip compile --quiet --refresh-package odm-api requirements-internal.txt > /dev/null && break; \
            [ $i -lt 60 ] && sleep 10 || exit 1; \
        done && \
        python3 -m tox run-parallel

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

    # Releases go to PyPI, development builds to TestPyPI
    ARG --required SDK_VERSION
    IF echo ${SDK_VERSION} | grep -Exq "^([0-9]+(.)?){3}$"
        ARG PYPI_REPOSITORY="https://upload.pypi.org/legacy/"
        ARG PYPI_TOKEN_SECRET="PYPI_TOKEN"
    ELSE
        ARG PYPI_REPOSITORY="https://test.pypi.org/legacy/"
        ARG PYPI_TOKEN_SECRET="PYPI_TOKEN_TEST"
    END

    # Push sdk
    RUN --push \
        --secret PYPI_TOKEN \
        --secret PYPI_TOKEN_TEST \
            TWINE_USERNAME=__token__ TWINE_PASSWORD="pypi-$(printenv ${PYPI_TOKEN_SECRET})" \
                twine upload dist/* --repository-url ${PYPI_REPOSITORY}

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
