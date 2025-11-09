#!/bin/bash
set -e

curr_dist="$(dpkg-parsechangelog -S Distribution)"
ver="$(dpkg-parsechangelog -S Version)"
if [[ "$curr_dist" != "UNRELEASED" ]]; then
	echo "Current distribution is $curr_dist, not UNRELEASED"
	# show current changelog entry for convenience
	dpkg-parsechangelog -S Changes
	exit 1
fi

dist="${1:-unstable}"
set -x
dch -r --no-force-save-on-release --distribution "$dist"
git commit debian/changelog -m "Release $ver to $dist"
if [[ -z "$NOTAG" ]]; then
	git tag -s "debian/${ver//[~]/_}" -m "Debian release $ver" -f
fi
