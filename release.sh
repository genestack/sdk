#! /bin/bash
set -e

# Get release version from version.py
RELEASE_VERSION=$(./setup.py --version)
echo "RELEASE_VERSION=${RELEASE_VERSION}"

# Check RTD_TOKEN env is exists.
if [[ -z "${RTD_TOKEN}" ]]; then
    echo "RTD_TOKEN isn't exists. Stop script."
    exit 1
else
    echo "RTD_TOKEN exists. Let's move on."
fi


# Check GITHUB_TOKEN env is exists.
if [[ -z "${GITHUB_TOKEN}" ]]; then
    echo "GITHUB_TOKEN isn't exists. Stop script."
    exit 1
else
    echo "GITHUB_TOKEN exists. Let's move on."
fi


# Check that python-client is builded
if [[ -d "dist" ]]; then
    echo "Python-client isn't builded. Stop script."
    exit 1
else
    echo "Python-client is builded. Let's move on."
fi


# Check that git tag with $RELEASE_VERSION is exists.
if git tag -l | grep -q ${RELEASE_VERSION}; then
    echo "v${RELEASE_VERSION} was found in git tags. Let's move on."
else
    echo "v${RELEASE_VERSION} wasn't found in git tags. top script."
    exit 1
fi


# Check that ChangeLog string with $RELEASE_VERSION is exists.
if grep -Fq ${RELEASE_VERSION} ChangeLog; then
    echo "${RELEASE_VERSION} was found in ChangeLog. Let's move on."
else
    echo "${RELEASE_VERSION} wasn't found in ChangeLog. Stop script."
    exit 1
fi


# Create Github release
curl \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/genestack/python-client/releases \
  -d '{"tag_name":"v'${RELEASE_VERSION}'","target_commitish":"master","name":"genestack-python-client-v'${RELEASE_VERSION}'","body":"Description of the release here: https://github.com/genestack/python-client/blob/v'${RELEASE_VERSION}'/ChangeLog","draft":false,"prerelease":false,"generate_release_notes":false}'


# Trigger Read the docs builds
curl \
  -X POST \
  -H "Authorization: Token ${RTD_TOKEN}" https://readthedocs.org/api/v3/projects/genestack-client/versions/latest/builds/
curl \
  -X POST \
  -H "Authorization: Token ${RTD_TOKEN}" https://readthedocs.org/api/v3/projects/genestack-client/versions/stable/builds/


# Push to pypi
twine upload dist/* -r testpypi
twine upload dist/*
