#!/bin/bash
#set -e

# cd to the script directory
CURDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

announce_info () {
	echo "[${PACKAGE}] $*" | tee "${ANNOUNCE_FIFO_TARGET}"
}

build_and_import () {
	# Build
	DEBEMAIL="$EMAIL" DEBFULLNAME="$NAME" dpkg-buildpackage -S -us -uc -d -sa
	sudo PBUILDER_DIST="$BUILD_DIST" cowbuilder --update
	mkdir -p "${OUTPUT_DIR}/${PACKAGE}_${DEBVERSION}"
	sudo PBUILDER_DIST="$BUILD_DIST" cowbuilder --build ../"${PACKAGE}_${DEBVERSION}.dsc" --buildresult "${OUTPUT_DIR}/${PACKAGE}_${DEBVERSION}"
	cd "${OUTPUT_DIR}/${PACKAGE}_${DEBVERSION}"

	aptly repo add "$TARGET_DIST" *.deb *.dsc

	announce_info "New files for ${TARGET_DIST}: " *.deb *.dsc
	announce_info "If you see a glob above, it probably means something went terribly wrong..."
}

autogit () {
	GIT_AUTHOR_EMAIL="$EMAIL" GIT_COMMITTER_EMAIL="$EMAIL" GIT_AUTHOR_NAME="$NAME" GIT_COMMITTER_NAME="$NAME" git "$@"
}

build_git () {
	PACKAGE="$1"
	BRANCH="${GITBUILDER_UPSTREAM_REMOTE}/${2}"
	PACKAGING_BRANCH="$3"

	cd "$CURDIR"
	echo "Building $PACKAGE using branch ${BRANCH}"
	cd "$PACKAGE"

	# Bump the version
	git fetch "$GITBUILDER_UPSTREAM_REMOTE"
	VERSION="$(git describe --tags ${BRANCH} 2>&1 | sed -r 's/-([0-9]+)-g([0-9a-f]+)$/+git\1~\2/' | sed -r 's/^([0-9.]+)-?(alpha|beta|a|b|rc)/\1~\2/')"
	DEBVERSION="${VERSION}${VERSION_SUFFIX}"

	echo "Checking out Git branch $PACKAGING_BRANCH"

	git checkout -f "$PACKAGING_BRANCH" || (echo "Failed to checkout Git branch $PACKAGING_BRANCH" && cd "$CURDIR" && return)
	autogit pull --no-edit  # Merge the packaging branch's changes too

	LASTVERSION="$(dpkg-parsechangelog --show-field Version)"
	if [[ "$DEBVERSION" == "$LASTVERSION" && "$FORCE_SAME_BUILD" != true ]]; then
		echo "[${PACKAGE}] Skipping build (new version $DEBVERSION would be the same as what we have)" | tee "${ANNOUNCE_FIFO_TARGET}"
		cd "$CURDIR" && return
	fi

	# Bump the version & commit changes.
	autogit merge --no-edit "$BRANCH"

	if [[ "$DEBVERSION" != "$LASTVERSION" ]]; then
		DEBEMAIL="$EMAIL" DEBFULLNAME="$NAME" dch -bv "$DEBVERSION" --distribution "$BUILD_DIST" "Auto-build." --force-distribution
		autogit commit "debian/" -m "Auto-building $PACKAGE version $DEBVERSION"
	fi

	# Generate the tarball
	echo "Generating tarball for ${PACKAGE}_${VERSION}.orig.tar.gz ..."
	git archive "$BRANCH" -o ../"${PACKAGE}_${VERSION}.orig.tar.gz"

	build_and_import
	cd "$CURDIR"
}

publish () {
	aptly publish update -gpg-key="$GPG_KEY" "$TARGET_DIST"
}

cleanup () {
    echo "Cleaning up..."
	rm -v *.tar.* *.buildinfo *.dsc *.changes
}
