#!/bin/bash

# Eventually we'll transition from sid to unstable...
aptly repo include -uploaders-file="/srv/aptly/urepo-uploaders.json" \
	-repo='{{if eq .Distribution "unstable"}}sid{{else}}{{.Distribution}}{{end}}' \
	-keyring="$HOME/.gnupg/pubring.gpg" \
    "$@" "/srv/aptly/incoming"
