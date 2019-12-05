#!/bin/bash

CURDIR=$(dirname "$(readlink -f "$0")")

cd "$CURDIR"
echo 'Sourcing config.sh'
source "config.sh"
echo 'Sourcing buildercore.sh'
source "buildercore.sh"

# Repositories to build. Args to build_git:
#    package name (a subfolder in the autobuilder folder),
#    upstream branch to merge (will run git merge $GITBUILDER_UPSTREAM_REMOTE/<this field>)
#    branch containing packaging (the branch to merge into)
build_git "youtube-dl" "master" "master"
build_git "you-get" "develop" "utopia-nightly"

publish
sleep 3

echo 'Sourcing config-buster.sh'; source "config-buster.sh"

build_git "youtube-dl" "master" "buster-nightlies"
build_git "you-get" "develop" "buster-nightlies"
publish

cleanup
