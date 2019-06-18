#!/bin/bash
#set -e

# cd to the script directory
CURDIR=$(dirname "$(readlink -f "$0")")

announce_info () {
	text="[${PACKAGE}] $*"
	echo "$text"
	irk "$ANNOUNCE_IRKER_TARGET" "$text"
}

echo "Using OUTPUT_DIR $OUTPUT_DIR"

build_and_import () {
	if [[ "$UTOPIAAB_DRY_RUN" != true ]]; then # read env var
		# Build
		echo "Building .dsc in $(pwd)"
		DEBEMAIL="$EMAIL" DEBFULLNAME="$NAME" dpkg-buildpackage -S -us -uc -d -sa
		if [[ $? -eq 0 ]]; then
			sudo PBUILDER_DIST="$BUILD_DIST" cowbuilder --update

			PKGDIR="${OUTPUT_DIR}/${PACKAGE}_${DEBVERSION}"
			mkdir -p "$PKGDIR"

			echo "Building .debs in $(pwd)"
			sudo PBUILDERSATISFYDEPENDSCMD=/usr/lib/pbuilder/pbuilder-satisfydepends-apt \
				PBUILDER_DIST="$BUILD_DIST" cowbuilder --build "../${PACKAGE}_${DEBVERSION}.dsc" --buildresult "${PKGDIR}" \
				&& aptly repo remove "$TARGET_DIST" "\$Source ($PACKAGE) | $PACKAGE"
			aptly repo add "$TARGET_DIST" "$PKGDIR"/*.deb "$PKGDIR"/*.dsc
			if [[ $? -eq 0 ]]; then
				announce_info "New build for ${TARGET_DIST}: ${PACKAGE}_${DEBVERSION}"
			else
				announce_info "Failed to add files for this package, check the logs for details."
			fi
		else
			announce_info "Generating .dsc failed"
		fi
	else
		echo "Skipping actual build as UTOPIAAB_DRY_RUN was set..."
	fi
}

autogit () {
	echo "Running git $@"
	GIT_AUTHOR_EMAIL="$EMAIL" GIT_COMMITTER_EMAIL="$EMAIL" GIT_AUTHOR_NAME="$NAME" GIT_COMMITTER_NAME="$NAME" git "$@"
}

# In order: convert git commit to +git~commithash format,
#           mangle prereleases into ~alpha1, etc.
#           remove non-numeric headers if any
cleanup_version () {
	echo "$(sed -r 's/-([0-9]+)-g([0-9a-f]+)$/+git\1~\2/' <<< $1 | sed -r 's/^([0-9.]+)-?(alpha|beta|a|b|rc)/\1~\2/' | sed -r 's/^(([^0-9])+?)//')"
}

build_git () {
	PACKAGE="$1"
	BRANCH="${GITBUILDER_UPSTREAM_REMOTE}/${2}"
	PACKAGING_BRANCH="$3"

	echo "Building $PACKAGE using branch ${BRANCH}"
	pushd "$CURDIR"
	pushd "$PACKAGE"

	# Bump the version
	git fetch "$GITBUILDER_UPSTREAM_REMOTE"
	VERSION="$(cleanup_version $(git describe --tags ${BRANCH} 2>&1))"
	DEBVERSION="${VERSION}${VERSION_SUFFIX}"

	echo "Checking out Git branch $PACKAGING_BRANCH"

	git checkout -f "$PACKAGING_BRANCH" || (echo "Failed to checkout Git branch $PACKAGING_BRANCH" && cd "$CURDIR" && return)
	# Trash the last (temporary) changelog entry
	git checkout debian/changelog
	autogit pull --no-edit  # Merge the packaging branch's changes too

	VERSIONFILE="debian/.utopiaab_last_version_${BUILD_DIST}"

	LASTVERSION="$(cat $VERSIONFILE)"

	echo "[$PACKAGE] Checking if package version $DEBVERSION <= $LASTVERSION"
	# Grab exit code from dpkg comparison
	dpkg --compare-versions "$DEBVERSION" '<=' "$LASTVERSION"
	if [[ $? -eq 0 && "$UTOPIAAB_FORCE_REBUILD" != true ]]; then
		announce_info "Skipping build (new version $DEBVERSION is <= what we have)"
		popd; return
	fi

	# Bump the version & commit changes.
	autogit merge --no-edit --no-commit "$BRANCH"

	DEBEMAIL="$EMAIL" DEBFULLNAME="$NAME" dch -bv "$DEBVERSION" --distribution "$BUILD_DIST" "Auto-build." --force-distribution
	if [[ $? -ne 0 ]]; then
		announce_info "dch invocation failed"
		popd; return
	fi
	echo "Saving build version $DEBVERSION to $VERSIONFILE"
	echo "$DEBVERSION" > "$VERSIONFILE"

	# Generate the tarball
	echo "Generating tarball for ${PACKAGE}_${VERSION}.orig.tar.gz ..."
	git archive "$BRANCH" -o "../${PACKAGE}_${VERSION}.orig.tar.gz"
	if [[ $? -ne 0 ]]; then
		announce_info "orig tarball generation FAILED"
	else
		build_and_import
	fi
	popd  # Return to the last folder
}

publish () {
	if [[ "$UTOPIAAB_DRY_RUN" != true ]]; then
		aptly publish update -gpg-key="$GPG_KEY" "$TARGET_DIST"
	fi
}

cleanup () {
	if [[ "$UTOPIAAB_DRY_RUN" != true ]]; then
	    echo "Cleaning up..."
		rm -v *.tar.* *.buildinfo *.dsc *.changes
	fi
}
