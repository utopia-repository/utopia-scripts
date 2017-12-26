#!/bin/bash
#set -e

# cd to the script directory
CURDIR=$(dirname "$(readlink -f "$0")")

announce_info () {
	echo "[${PACKAGE}] $*" | tee "${ANNOUNCE_FIFO_TARGET}"
}

echo "Using OUTPUT_DIR $OUTPUT_DIR"

build_and_import () {
	if [[ "$UTOPIAAB_DRY_RUN" != true ]]; then # read env var
		# Build
		echo "Building .dsc in $(pwd)"
		DEBEMAIL="$EMAIL" DEBFULLNAME="$NAME" dpkg-buildpackage -S -us -uc -d -sa
		sudo PBUILDER_DIST="$BUILD_DIST" cowbuilder --update

		PKGDIR="${OUTPUT_DIR}/${PACKAGE}_${DEBVERSION}"
		mkdir -p "$PKGDIR"

		echo "Building .debs in $(pwd)"
		sudo PBUILDER_DIST="$BUILD_DIST" cowbuilder --build "../${PACKAGE}_${DEBVERSION}.dsc" --buildresult "${PKGDIR}"

		aptly repo add "$TARGET_DIST" "$PKGDIR"/*.deb "$PKGDIR"/*.dsc
		if [[ $? -eq 0 ]]; then
			announce_info "New files for ${TARGET_DIST}: " "${OUTPUT_DIR}/${PACKAGE}_${DEBVERSION}"/*.deb "${OUTPUT_DIR}/${PACKAGE}_${DEBVERSION}"/*.dsc
		else
			announce_info "Failed to add files for this package, check the logs for details."
		fi
	else
		echo "Skipping actual build as UTOPIAAB_DRY_RUN was set..."
	fi
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
	# Trash the last (temporary) changelog entry
	git checkout debian/changelog
	autogit pull --no-edit  # Merge the packaging branch's changes too

	VERSIONFILE=".utopiaab_last_version_${BUILD_DIST}"

	LASTVERSION="$(cat $VERSIONFILE)"
	if [[ "$DEBVERSION" == "$LASTVERSION" && "$UTOPIAAB_FORCE_REBUILD" != true ]]; then
		echo "[${PACKAGE}] Skipping build (new version $DEBVERSION would be the same as what we have)" | tee "${ANNOUNCE_FIFO_TARGET}"
		cd "$CURDIR" && return
	fi

	# Bump the version & commit changes.
	autogit merge --no-edit --no-commit "$BRANCH"

	if [[ "$DEBVERSION" != "$LASTVERSION" ]]; then
		DEBEMAIL="$EMAIL" DEBFULLNAME="$NAME" dch -bv "$DEBVERSION" --distribution "$BUILD_DIST" "Auto-build." --force-distribution
		echo "Saving build version $DEBVERSION to $VERSIONFILE"
		echo "$DEBVERSION" > "$VERSIONFILE"
	fi

	# Generate the tarball
	echo "Generating tarball for ${PACKAGE}_${VERSION}.orig.tar.gz ..."
	git archive "$BRANCH" -o "../${PACKAGE}_${VERSION}.orig.tar.gz"

	build_and_import
}

publish () {
	if [[ "$UTOPIAAB_DRY_RUN" != true ]]; then
		aptly publish update -gpg-key="$GPG_KEY" "$TARGET_DIST"
	fi
}

cleanup () {
	if [[ "$UTOPIAAB_DRY_RUN" != true ]]; then
	    echo "Cleaning up..."
		cd "$CURDIR"
		rm -v *.tar.* *.buildinfo *.dsc *.changes
	fi
}
