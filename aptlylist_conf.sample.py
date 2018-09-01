import os.path
### Configuration file for aptlylist.py

# Sets the folder where the generated package lists should go. This should be the same folder that
# contains the public dists/ and pool/ folders.
OUTDIR = "/srv/aptly/public"

# A list of repositories to parse.
TARGET_DISTS = ["sid", "sid-imports", "sid-forks", "experimental",
                "stretch", "stretch-imports", "stretch-forks",
                "bionic", "bionic-imports", "bionic-forks",
                "xenial"]

# REGEX to look for snapshots for the distribution we're looking up. Defaults to ${dist}-YYYY-MM-DD.
# If this regex doesn't match a certain distribution, it is treated as its own repository in lookup.
SNAPSHOT_REGEX = r'^%s-\d{4}-\d{2}-\d{2}'  # First %s is the distribution name

# Determines whether we should experimentally create pool/ links to each package entry. This may be
# time consuming for larger repositories, because the script will index the entirety of pool/.
SHOW_POOL_LINKS = True

# Determines whether changelogs should be shown generated, using the format of synaptic
# (i.e. PACKAGENAME_VERSION_ARCH.changelog).
# This option requires the python3-debian module, and implies that 'SHOW_POOL_LINKS' is enabled.
# This may be time consuming for repositories with large .deb's, as each .deb is temporarily
# extracted to retrieve its changelog.
SHOW_CHANGELOGS = True

# The directory that changelogs should be written to.
CHANGELOG_TARGET_DIR = os.path.join(OUTDIR, "changelogs")

# Determines the maximum file size (in bytes) for .deb's that this script should read to
# generate changelogs. Any files larger than this size will be skipped.
MAX_CHANGELOG_FILE_SIZE = 20971520  # 20 MB

# Determines whether Vcs-Browser links should be shown. This may be time consuming for larger
# repositories, since a package information call is made to aptly for every package in the repository.
SHOW_VCS_LINKS = True

# Determines whether package descriptions should be shown as tooltips in the package name field.
# This may be time consuming for larger repositories, since a package information call is made to aptly
# for every package in the repository.
SHOW_DESCRIPTIONS = True

# Determines whether dependencies/recommends/suggests for packages should be shown.
# This may be time consuming for larger repositories, since a package information call is made to aptly
# for every package in the repository.
SHOW_DEPENDENCIES = True

# Determines whether extended package relations (Breaks/Conflicts/Replaces) will be shown.
# This can be added for completeness but usually isn't of great value to end users.
# This option requires SHOW_DEPENDENCIES to be enabled.
SHOW_EXTENDED_RELATIONS = False

# Defines any CSS, code, etc. to put in <head>.
# The resources for my site are over at https://git.overdrivenetworks.com/james/ureposite
EXTRA_STYLES = """<link rel="stylesheet" type="text/css" href="gstyle.css">
<!-- From http://www.kryogenix.org/code/browser/sorttable/ -->
<script src="sorttable.js"></script>
"""
