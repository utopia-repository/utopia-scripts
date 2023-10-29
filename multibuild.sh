#!/bin/bash
# Build a package on multiple cowbuilder chroots
set -e

# Root directory for outputs
MULTIBUILD_OUTPUT_DIR="${MULTIBUILD_OUTPUT_DIR:-/srv/packages}"

print_usage() {
    echo "Usage: $0 <.dsc to build> <distribution 1> [<distribution 2> ...]"
    echo "This tool expects the pbuilder BASEPATH variable to look at the DIST variable"
    echo "Set the MULTIBUILD_FLAGS variable to pass other flags to cowbuilder"
    echo "Set the MULTIBUILD_OUTPUT_DIR variable to override default build dir /srv/packages"
    exit 1
}

read_vars() {
    . /usr/share/pbuilder/pbuilderrc
    . /etc/pbuilderrc
}

DSC="$1"
if [[ -z "$2" ]]; then
    print_usage
fi
shift

for dist in "$@"; do
    export DIST="$dist"
    read_vars

    if [[ -z "$BASEPATH" ]]; then
        echo 'Error: BASEPATH variable not set after reading pbuilderrc'
        exit 1
    elif [[ ! -d "$BASEPATH" ]]; then
        echo "Error: BASEPATH dir $BASEPATH does not exist"
        exit 1
    fi
    pkg_version_pair="$(basename "$DSC")"
    outdir="$MULTIBUILD_OUTPUT_DIR/${pkg_version_pair%.*}/$dist/"
    mkdir -p "$outdir"
    echo "Building \"$DSC\" on $dist using chroot $BASEPATH"
    sudo DIST="$dist" cowbuilder --update
    sudo DEPS="$DEPS" DIST="$dist" cowbuilder --build "$DSC" --buildresult "$outdir" $MULTIBUILD_FLAGS
done
