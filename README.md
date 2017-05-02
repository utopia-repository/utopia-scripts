This repository contains some scripts I use for my personal APT repository @ http://packages.overdrivenetworks.com/

### Contents

##### aptlylist.py
 * Generate HTML package listings for [aptly](https://github.com/smira/aptly) Debian repositories.

##### aptlysc.py
 * A hacky automation wrapper for aptly.

##### depends.py
 * Output dependency info from a package's `debian/control` file. Uses STDIN and STDOUT for input/output.

##### installcheck.py
 * Check package installability in APT repositories - a fully automatic wrapper for [dose-debcheck](https://qa.debian.org/dose/debcheck.html).

##### snapshots.py
 * Snapshot update announcer for aptly servers.
