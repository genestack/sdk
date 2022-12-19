#! /bin/bash
set -ex

# These script are created for executing inside Earthfile build.

#
## Check that git tag with $RELEASE_VERSION is exists.

#
#
## Check that ChangeLog string with $RELEASE_VERSION is exists.
#if ; then
#    echo "${RELEASE_VERSION} was found in ChangeLog. Let's move on."
#else
#    echo "${RELEASE_VERSION} wasn't found in ChangeLog. Stop script."
#    exit 1
#fi

git config user.name ${GITHUB_USER}
git config user.email ${GITHUB_USER_EMAIL}


git checkout tmp/test1
git pull
git checkout stable
git merge tmp/test2
#git push
#
#
## Set version tag:
#git tag -l | xargs git tag -d
#git fetch --tags
#git tag v${RELEASE_VERSION}
#git push --tags# Merge master into stable



## Create Github release
#curl \
#  -X POST \
#  -H "Accept: application/vnd.github+json" \
#  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
#  -H "X-GitHub-Api-Version: 2022-11-28" \
#  https://api.github.com/repos/genestack/python-client/releases \
#  -d '{"tag_name":"v'${RELEASE_VERSION}'","target_commitish":"master","name":"genestack-python-client-v'${RELEASE_VERSION}'","body":"Description of the release here: https://github.com/genestack/python-client/blob/v'${RELEASE_VERSION}'/ChangeLog","draft":false,"prerelease":false,"generate_release_notes":false}'
#
#
## Trigger Read the docs builds
#curl \
#  -X POST \
#  -H "Authorization: Token ${RTD_TOKEN}" https://readthedocs.org/api/v3/projects/genestack-client/versions/latest/builds/
#curl \
#  -X POST \
#  -H "Authorization: Token ${RTD_TOKEN}" https://readthedocs.org/api/v3/projects/genestack-client/versions/stable/builds/
#
#
## Push to pypi
#twine upload dist/* -r testpypi
#twine upload dist/*
