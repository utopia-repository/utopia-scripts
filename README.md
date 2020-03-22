Backend automation scripts for [the Utopia Repository](https://deb.utopia-repository.org).

### Highlights

##### autobuilder/
 * A custom nightly builds toolchain using Git repositories and cowbuilder.

##### aptlylist2.py
 * Generate HTML package listings for [aptly](https://github.com/smira/aptly) Debian repositories.
 * Also supports creating download URLs, extracting changelogs, and checking uscan status (`debian/watch`)

##### installcheck.py
 * Check package installability in APT repositories - a fully automatic wrapper for [dose-debcheck](https://qa.debian.org/dose/debcheck.html).

##### snapshots.py
 * Snapshot update announcer for aptly servers.
