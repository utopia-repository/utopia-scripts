#!/bin/bash
#set -e

# cd to the script directory
CURDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

announce_info () {
	echo "[${PACKAGE}] $*" | tee "${ANNOUNCE_FIFO_TARGET}"
}

build_and_import () {
	# Build
	DEBEMAIL="$EMAIL" DEBFULLNAME="$NAME" dpkg-buildpackage -S -us -uc -d
	sudo PBUILDER_DIST="$BUILD_DIST" cowbuilder --update
	mkdir -p "${OUTPUT_DIR}/${PACKAGE}_${DEBVERSION}"
	sudo PBUILDER_DIST="$BUILD_DIST" cowbuilder --build ../"${PACKAGE}_${DEBVERSION}.dsc" --buildresult "${OUTPUT_DIR}/${PACKAGE}_${DEBVERSION}"
	cd "${OUTPUT_DIR}/${PACKAGE}_${DEBVERSION}"

	aptly repo add "$TARGET_DIST" *.deb *.dsc

	announce_info "New files for ${TARGET_DIST}: " *.deb *.dsc
	announce_info "If you see a glob above, it probably means something went terribly wrong..."
}

build_git () {
	PACKAGE="$1"
	BRANCH="$2"

	cd "$CURDIR"
	echo "Building $PACKAGE using branch ${BRANCH}"
	cd "$PACKAGE"

	# Bump the version
	git fetch "$UPSTREAM_REMOTE"
	VERSION="$(git describe --tags ${BRANCH} 2>&1 | sed -r 's/-([0-9]+)-g([0-9a-f]+)$/+git\1~\2/' | sed -r 's/^([0-9.]+)-?(alpha|beta|a|b|rc)/\1~\2/')"
	DEBVERSION="${VERSION}${VERSION_SUFFIX}"

	if [[ "$DEBVERSION" == "$(dpkg-parsechangelog --show-field Version)" ]]; then
		echo "[${PACKAGE}] Skipping build (new version $DEBVERSION would be the same as what we have)" | tee "${ANNOUNCE_FIFO_TARGET}"
		return
	fi

	# Merge with upstream
	git stash
	GIT_AUTHOR_EMAIL="$EMAIL" GIT_COMMITTER_EMAIL="$EMAIL" GIT_AUTHOR_NAME="$NAME" GIT_COMMITTER_NAME="$NAME" git merge --no-edit "$BRANCH"
	DEBEMAIL="$EMAIL" DEBFULLNAME="$NAME" dch -v "$DEBVERSION" --distribution unstable "Auto-build."

	# Generate the tarball
	git archive "$BRANCH" -o ../"${PACKAGE}_${VERSION}.orig.tar.gz"

	build_and_import
}

publish () {
	aptly publish update -gpg-key="$GPG_KEY" "$TARGET_DIST"
}
