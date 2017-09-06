#!/bin/bash

# Suffix to replace the Debian package revision with
VERSION_SUFFIX="-0utopia0~autobuild~deb9u1"

# Note: no trailing / for OUTPUT_DIR
OUTPUT_DIR="../builds"

# Target aptly distribution
TARGET_DIST="stretch-nightlies"

# Distribution variable passed into cowbuilder, if you use multiple chroots
BUILD_DIST="stretch"
