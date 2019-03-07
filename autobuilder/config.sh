#!/bin/bash

# Remote name of the upstream sources in Git
GITBUILDER_UPSTREAM_REMOTE="upstream"

# Suffix to replace the Debian package revision with
VERSION_SUFFIX="-0utopia0~auto"

# Name and email used for dch and merge commits
NAME="Utopia Repository Auto-builder"
EMAIL="packages-admin@overdrivenetworks.com"

# Note: no trailing / for OUTPUT_DIR
OUTPUT_DIR="$(mktemp -d /tmp/utopiaab.XXXXXXXXXX)" || (echo "Failed to create OUTPUT_DIR" && exit 1)

# Target aptly distribution
TARGET_DIST="sid-nightlies"

# Distribution variable passed into cowbuilder, if you use multiple chroots
BUILD_DIST="unstable"

# GPG key to sign packages with
GPG_KEY="EEBB01E6"

# irker target
ANNOUNCE_IRKER_TARGET="irc://localhost:16667/dev"

# Determines whether we should force rebuild existing builds
FORCE_SAME_BUILD=false
