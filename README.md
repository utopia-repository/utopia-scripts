## packagelists/

This folder contains some scripts I use for my personal APT repository @ http://packages.overdrivenetworks.com/

### Contents

##### depends.py
 * Outputs dependency info from a package's `debian/control` file. Uses STDIN and STDOUT for input/output.

##### pparse3.py
 * Grabs repository listings from aptly's raw command line output.

##### aptlysc.py (*really bad code warning*)
 * A surprisingly hacky automation wrapper for aptly.
