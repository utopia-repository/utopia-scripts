#!/bin/bash
#set -e

# Map packages to the branches to update sources from. This script assumes that all source Git
# repositories listed here are subfolders in the same directory the script is in.
declare -A PACKAGES=([youtube-dl]="master" [pylink]="devel")

# Remote name of the upstream sources in Git
UPSTREAM_REMOTE="upstream"

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
BUILD_DIST="sid"

# GPG key to sign packages with
GPG_KEY="EEBB01E6"

# FIFO target (e.g. via ii to IRC) to announce to after the build is finished
ANNOUNCE_FIFO_TARGET="${HOME}/ii/irc.overdrivenetworks.com/#dev/in"

# cd to the script directory
CURDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
for PACKAGE in "${!PACKAGES[@]}"; do
	cd "$CURDIR"
	UPSTREAM_BRANCH="${UPSTREAM_REMOTE}/${PACKAGES[${PACKAGE}]}"
	echo "Building $PACKAGE using branch ${UPSTREAM_BRANCH}"
	cd "$PACKAGE"

	# Bump the version
	git fetch "$UPSTREAM_REMOTE"
	VERSION="$(git describe --tags ${UPSTREAM_BRANCH} 2>&1 | sed -r 's/-([0-9]+)-g([0-9a-f]+)$/+git\1~\2/' | sed -r 's/^([0-9.]+)-?(alpha|beta|a|b|rc)/\1~\2/')"
	DEBVERSION="${VERSION}${VERSION_SUFFIX}"

	if [[ "$DEBVERSION" == "$(dpkg-parsechangelog --show-field Version)" ]]; then
		echo "[${PACKAGE}] Skipping build (new version $DEBVERSION would be the same as what we have)" | tee "${ANNOUNCE_FIFO_TARGET}"
		continue
	fi

	# Merge with upstream
	git stash
	GIT_AUTHOR_EMAIL="$EMAIL" GIT_COMMITTER_EMAIL="$EMAIL" GIT_AUTHOR_NAME="$NAME" GIT_COMMITTER_NAME="$NAME" git merge --no-edit "$UPSTREAM_BRANCH"
	DEBEMAIL="$EMAIL" DEBFULLNAME="$NAME" dch -v "$DEBVERSION" --distribution unstable "Auto-build."

	# Generate the tarball
	git archive "$UPSTREAM_BRANCH" -o ../"${PACKAGE}_${VERSION}.orig.tar.gz"

	# Build
	DEBEMAIL="$EMAIL" DEBFULLNAME="$NAME" dpkg-buildpackage -S -us -uc -d
	#git stash pop
	sudo PBUILDER_DIST="$BUILD_DIST" cowbuilder --update
	mkdir -p "${OUTPUT_DIR}/${PACKAGE}_${DEBVERSION}"
	sudo PBUILDER_DIST="$BUILD_DIST" cowbuilder --build ../"${PACKAGE}_${DEBVERSION}.dsc" --buildresult "${OUTPUT_DIR}/${PACKAGE}_${DEBVERSION}"
	cd "${OUTPUT_DIR}/${PACKAGE}_${DEBVERSION}"

	echo "[${PACKAGE}] New files for ${TARGET_DIST}: " *.deb *.dsc | tee "${ANNOUNCE_FIFO_TARGET}"
	echo "[${PACKAGE}] If you see a glob above, it probably means something went terribly wrong..." | tee "${ANNOUNCE_FIFO_TARGET}"
	aptly repo add "$TARGET_DIST" *.deb *.dsc
	aptly publish update -gpg-key="$GPG_KEY" "$TARGET_DIST"
done
