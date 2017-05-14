#!/bin/bash

CURDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$CURDIR"

echo 'Sourcing config.sh'
source "config.sh"
echo 'Sourcing buildercore.sh'
source "buildercore.sh"

# Repositories to build
build_git "youtube-dl" "${UPSTREAM_REMOTE}/master"
