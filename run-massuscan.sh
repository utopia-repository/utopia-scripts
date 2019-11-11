# Runs massuscan on target dists
# Adjust the paths to fit your setup!

ANNOUNCE_IRKER_TARGET="ircs://irc.overdrivenetworks.com/#dev"
BASEURL="https://deb.utopia-repository.org/"
MASSUSCAN_PATH=~/utopia-scripts/massuscan.py

announce_info () {
    echo "$@"
    irk "$ANNOUNCE_IRKER_TARGET" "$@"
}


for dist in sid sid-forks sid-extras; do
	echo "Running massuscan for dist $dist"
    file="${dist}_uscan.html"
	"$MASSUSCAN_PATH" /srv/aptly/public/pool /srv/aptly/public/${dist}_sources.txt /srv/packages-qa/${file}

    count="$(grep 'newer package available' /srv/packages-qa/${file} | wc -l)"
    announce_info "Updated watch results for $dist: ${BASEURL}${file} - $count packages could be updated"
done

