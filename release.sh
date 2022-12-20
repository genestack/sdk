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


