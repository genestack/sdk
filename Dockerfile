# syntax=docker/dockerfile:1.29
#
# odm-sdk, the Python client of ODM, published as an sdist: to PyPI for a release version
# (X.Y.Z), to TestPyPI otherwise. No image. The build context is this repo, filtered by
# .dockerignore. The Makefile builds these targets:
#
#   sdist        the sdist; no tests. `make push` builds it with IMAGE_PUSH docker or none
#   pypi-upload  the sdist, uploaded by twine. `make push` builds it with IMAGE_PUSH registry
#                or full, as CI does
#   test         tox run-parallel: pytest on the image's Python
#   sonarcloud   the SonarCloud analysis
#
# odm-sdk pins the odm-api (the generated OpenAPI client) of OPENAPI_VERSION: setup.py
# reads it from requirements-internal.txt, which sdist and test render from its envtpl.

ARG UV_IMAGE=astral/uv:0.13.8-python3.15-alpine
ARG SONAR_SCANNER_IMAGE=sonarsource/sonar-scanner-cli:5.0.1

FROM ${UV_IMAGE} AS tox

# uv's cache is a cache mount, on another filesystem than the environments it installs
# into: copy from it, without the warning that hardlinks fail.
ENV UV_LINK_MODE=copy
WORKDIR /app

COPY requirements-tox.txt tox.ini ./
RUN --mount=type=cache,target=/root/.cache \
    uv pip install --system -r requirements-tox.txt

FROM tox AS test

COPY requirements-internal.txt.envtpl requirements-build.txt requirements-test.txt requirements.txt \
     uv.toml MANIFEST.in README.md LICENSE.txt setup.py ./
COPY odm_sdk/ odm_sdk/

# odm-api development builds are on TestPyPI, releases on PyPI. tox-uv installs with the
# image's uv, which uv.toml lets fall back to TestPyPI only for what PyPI lacks.
# TestPyPI's CDN can serve an index without a new version for up to 10 minutes after its
# upload (Cache-Control: max-age=600), so odm-api is resolved first, retried until the
# index lists it; tox's uv then reads that page from the same cache.
ARG OPENAPI_VERSION
RUN --mount=type=cache,target=/root/.cache \
    uvx envsubst < requirements-internal.txt.envtpl > requirements-internal.txt \
 && for i in $(seq 60); do \
        uv pip compile --quiet --refresh-package odm-api requirements-internal.txt > /dev/null && break; \
        [ "$i" -lt 60 ] && sleep 10 || exit 1; \
    done \
 && python3 -m tox run-parallel

# The push path: no tox, no tests. setup.py runs on the image's Python, with the setuptools
# and twine of requirements-build.txt.
FROM ${UV_IMAGE} AS sdist

ENV UV_LINK_MODE=copy
WORKDIR /app

COPY requirements-build.txt ./
RUN --mount=type=cache,target=/root/.cache \
    uv pip install --system -r requirements-build.txt

COPY requirements-internal.txt.envtpl requirements-test.txt requirements.txt \
     MANIFEST.in README.md LICENSE.txt setup.py ./
COPY odm_sdk/ odm_sdk/

ARG OPENAPI_VERSION
ARG SDK_VERSION
RUN --mount=type=cache,target=/root/.cache \
    uvx envsubst < requirements-internal.txt.envtpl > requirements-internal.txt \
 && uvx envsubst < odm_sdk/version.py.envtpl > odm_sdk/version.py \
 && python3 setup.py sdist

FROM ${SONAR_SCANNER_IMAGE} AS sonarcloud

ARG GIT_BRANCH_NAME

# The scanner analyses its working directory, which the image sets to /usr/src. It reads
# the history for blame and new-code detection from .git, which .dockerignore keeps out
# of the context: the Makefile passes it as the `git_dir` named context.
WORKDIR /usr/src
COPY . .
# git_dir is a named build context, not an image.
# hadolint ignore=DL3022
COPY --from=git_dir . .git

RUN --mount=type=secret,id=SONAR_TOKEN,env=SONAR_TOKEN \
    sonar-scanner -Dsonar.branch.name="${GIT_BRANCH_NAME}"

# Releases go to PyPI, development builds to TestPyPI, each with its own token.
FROM sdist AS pypi-upload

ARG SDK_VERSION
RUN --mount=type=secret,id=PYPI_TOKEN,env=PYPI_TOKEN \
    --mount=type=secret,id=PYPI_TOKEN_TEST,env=PYPI_TOKEN_TEST \
    if echo "${SDK_VERSION}" | grep -Exq "^([0-9]+(.)?){3}$"; then \
        repository=https://upload.pypi.org/legacy/; token="${PYPI_TOKEN}"; \
    else \
        repository=https://test.pypi.org/legacy/; token="${PYPI_TOKEN_TEST}"; \
    fi \
 && TWINE_USERNAME=__token__ TWINE_PASSWORD="pypi-${token}" \
        twine upload --repository-url "${repository}" dist/*
