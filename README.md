## packagelists/

This folder contains some scripts I use for my personal APT repository @ http://packages.overdrivenetworks.com/

### Contents

##### aptlysc.py
 * A surprisingly hacky automation wrapper for [aptly](https://github.com/smira/aptly).

##### depends.py
 * Outputs dependency info from a package's `debian/control` file. Uses STDIN and STDOUT for input/output.

##### pparse3.py
 * Grabs repository listings from aptly's raw command line output.

##### genchanges/
 * Generates changelogs from .deb's and writes them to a .changelog file.
