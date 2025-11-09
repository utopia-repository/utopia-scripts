#!/bin/bash
set -e

if [[ -z "$1" ]]; then
    echo "usage: $0 <new package version>"
    echo "Bump a Debian package's changelog version and commit the change to git"
    exit 1
fi

ver="$1"
shift
set -x
dch -v "$ver" -m "New upstream release." "$@"
git commit debian/changelog -m "Bump changelog to $ver"
