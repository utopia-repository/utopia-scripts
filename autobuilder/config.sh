#!/bin/bash

# Remote name of the upstream sources in Git
GITBUILDER_UPSTREAM_REMOTE="upstream"

# Default branch name (for "unstable" packaging content)
GITBUILDER_DEFAULT_BRANCH="master"

# Suffix to replace the Debian package revision with
VERSION_SUFFIX="-0utopia0~autobuild"

# Name and email used for dch and merge commits
NAME="Utopia Repository Auto-builder"
EMAIL="webmaster@overdrivenetworks.com"

# Note: no trailing / for OUTPUT_DIR
OUTPUT_DIR="../builds"

# Target aptly distribution
TARGET_DIST="sid-nightlies"

# Distribution variable passed into cowbuilder, if you use multiple chroots
BUILD_DIST="unstable"

# GPG key to sign packages with
GPG_KEY="EEBB01E6"

# FIFO target (e.g. via ii to IRC) to announce to after the build is finished
ANNOUNCE_FIFO_TARGET="${HOME}/ii/irc.overdrivenetworks.com/#dev/in"
