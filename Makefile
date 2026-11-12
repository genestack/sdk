# Setting SHELL to bash allows bash commands to be executed by recipes.
# Options are set to exit when a recipe line exits non-zero or a piped command fails.
SHELL = /usr/bin/env bash -o pipefail
.SHELLFLAGS = -ec

# The version odm-sdk is published under: CI's Push and Test builds set IMAGE_VERSION in
# every repo, image or not. A release version (X.Y.Z) goes to PyPI, any other to TestPyPI.
IMAGE_VERSION ?= 1.0.0

.PHONY: main
main: push

##@ General

# The help target prints out all targets with their descriptions organized
# beneath their categories. The categories are represented by '##@' and the
# target descriptions by '##'. The awk command is responsible for reading the
# entire set of makefiles included in this invocation, looking for lines of the
# file as xyz: ## something, and then pretty-format the target and help. Then,
# if there's a line with ##@ something, that gets pretty-printed as a category.
# More info on the usage of ANSI control characters for terminal formatting:
# https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_parameters
# More info on the awk command:
# http://linuxcommand.org/lc3_adv_awk.php

.PHONY: help
help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Build

# In CI the Vault step writes every secret to .secret in the checkout (teamcity-main's
# templates/Vault.kt); only the PyPI tokens go into the build.
.PHONY: push
push: ## Build the sdist of IMAGE_VERSION against odm-api OPENAPI_VERSION and upload it, without tests: PyPI for X.Y.Z, TestPyPI otherwise.
	@if [ -f .secret ]; then set -a; . ./.secret; set +a; fi; \
	docker buildx build \
	--target=push \
	--build-arg=SDK_VERSION=$(IMAGE_VERSION) \
	--build-arg=OPENAPI_VERSION=$(or $(OPENAPI_VERSION),$(error OPENAPI_VERSION is not set)) \
	--secret=id=PYPI_TOKEN,env=PYPI_TOKEN \
	--secret=id=PYPI_TOKEN_TEST,env=PYPI_TOKEN_TEST \
	--no-cache-filter=push \
	--output=type=cacheonly \
	.

.PHONY: test
test: ## Run tox run-parallel (pytest) against odm-api OPENAPI_VERSION.
	docker buildx build \
	--target=test \
	--build-arg=OPENAPI_VERSION=$(or $(OPENAPI_VERSION),$(error OPENAPI_VERSION is not set)) \
	--output=type=cacheonly \
	.

.PHONY: sonarcloud
sonarcloud: ## Send the analysis of GIT_BRANCH_NAME to SonarCloud, with SONAR_TOKEN from .secret or the environment.
	@if [ -f .secret ]; then set -a; . ./.secret; set +a; fi; \
	docker buildx build \
	--target=sonarcloud \
	--build-context=git_dir=.git \
	--build-arg=GIT_BRANCH_NAME=$(or $(GIT_BRANCH_NAME),$(error GIT_BRANCH_NAME is not set)) \
	--secret=id=SONAR_TOKEN,env=SONAR_TOKEN \
	--no-cache-filter=sonarcloud \
	--output=type=cacheonly \
	.
