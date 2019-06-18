Backend automation scripts for [the Utopia Repository](https://deb.utopia-repository.org).

### Contents

##### autobuilder/
 * A custom nightly builds toolchain using Git repositories and cowbuilder.

##### aptlylist.py
 * Generate HTML package listings for [aptly](https://github.com/smira/aptly) Debian repositories.

##### aptlysc.py
 * Miscellaneous automation wrapper for aptly.

##### installcheck.py
 * Check package installability in APT repositories - a fully automatic wrapper for [dose-debcheck](https://qa.debian.org/dose/debcheck.html).

##### massuscan.py
 * Checks watch files on all non-native packages in a repository. Live @ https://qa.deb.utopia-repository.org/

##### snapshots.py
 * Snapshot update announcer for aptly servers.
