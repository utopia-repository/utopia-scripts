#!/bin/bash
# Runs 'aptly include' on every subdir of an incoming root directory,
# where each subdir contains packages for a repo of the same name.

UPLOADERS_FILE="/srv/aptly/urepo-uploaders.json"
INCOMING_ROOT="/srv/aptly/incoming"

#set -x

for dir in "${INCOMING_ROOT}/"*/; do
	dist="$(basename "$dir")"
	echo "Processing dist $dist from directory $dir ..."
	aptly repo include -uploaders-file="$UPLOADERS_FILE" \
		-keyring="$HOME/.gnupg/pubring.kbx" \
		-repo="$dist" \
		"$@" "$dir"
done
