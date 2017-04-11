#!/usr/bin/env python3
"""
HTML package listing script for aptly servers, as seen on https://packages.overdrivenetworks.com
This looks up snapshots related to repositories and mirror, and creates tables showing each
package's name, version, and architecture. It also supports optionally displaying links to
.deb/.dsc downloads, listing package relations (e.g. dependencies), and generating changelogs.
"""
import time
import subprocess
import sys
import shutil
import os
import re
import traceback
import collections

### BEGIN CONFIGURATION VARIABLES ###

# Sets the folder where the generated package lists should go. This should be the same folder that
# contains the public dists/ and pool/ folders.
OUTDIR = "/srv/aptly/public"

# A list of repositories is automatically retrieved, but you can define extra distributions to
# process here.
EXTRA_DISTS = ["sid-imports"]

# REGEX to look for snapshots for the distribution we're looking up. Defaults to ${dist}-YYYY-MM-DD.
# If this regex doesn't match a certain distribution, it is treated as its own repository in lookup.
SNAPSHOT_REGEX_BASE = r'^%s-\d{4}-\d{2}-\d{2}'  # First %s is the distribution name

# Determines whether we should experimentally create pool/ links to each package entry. This may be
# time consuming for larger repositories, because the script will index the entirety of pool/.
SHOW_POOL_LINKS = True

# Determines whether changelogs should be shown generated, using the format of synaptic
# (i.e. PACKAGENAME_VERSION_ARCH.changelog).
# This option requires the python3-debian module, and implies that 'SHOW_POOL_LINKS' is enabled.
# This may be time consuming for repositories with large .deb's, as each .deb is temporarily
# extracted to retrieve its changelog.
SHOW_CHANGELOGS = True

# Defines a changelog cache directory: generated changelogs will be stored here and reused, instead
# of regenerating changelogs for versions already known.
CHANGELOG_CACHE_DIR = "/srv/aptly/changelogcache"

# Determines the maximum file size (in bytes) for .deb's that this script should read to
# generate changelogs. Any files larger than this size will be skipped.
MAX_CHANGELOG_FILE_SIZE = 20971520  # 20 MB

# Determines whether Vcs-Browser links should be shown.
SHOW_VCS_LINKS = True

# Determines whether dependencies/recommends/suggests for packages should be shown.
SHOW_DEPENDENCIES = True

# Determines whether extended package relations (Breaks/Conflicts/Replaces) will be shown.
# This can be added for completeness but usually isn't of great value to end users.
SHOW_EXTENDED_RELATIONS = False

# Defines any extra styles / lines to put in <head>.
# The gstyle.css for packages.o.c can be found at https://git.io/vSKJj for reference
EXTRA_STYLES = """<link rel="stylesheet" type="text/css" href="gstyle.css">
<!-- From http://www.kryogenix.org/code/browser/sorttable/ -->
<script src="sorttable.js"></script>
"""

### END CONFIGURATION VARIABLES ###

if SHOW_CHANGELOGS:
    from debian import changelog, debfile

if not shutil.which('aptly'):
    print('Error: aptly not found in path!')
    sys.exit(1)

print('Output directory set to: %s' % OUTDIR)
repolist = subprocess.check_output(("aptly", "repo", "list", "-raw")).decode('utf-8').splitlines()
repolist += EXTRA_DISTS
snapshotlist = subprocess.check_output(("aptly", "snapshot", "list", "-raw")).decode('utf-8').splitlines()

if SHOW_POOL_LINKS or SHOW_CHANGELOGS:  # Pre-enumerate a list of all objects in pool/
    import pathlib
    # XXX: ugly globs......
    poolobjects = list(pathlib.Path(OUTDIR).glob('pool/*/*/*/*.*'))

    if CHANGELOG_CACHE_DIR and not os.path.exists(CHANGELOG_CACHE_DIR):
        print("Creating cache dir %s" % CHANGELOG_CACHE_DIR)
        os.mkdir(CHANGELOG_CACHE_DIR)

DEPENDENCY_TYPES = {"Build-Depends": 'build-dep', "Build-Depends-Indep": 'build-idep',
                    "Depends": 'dep', "Recommends": 'rec', "Suggests": 'sug',
                    "Enhances": 'enh',
# Not sure whether Provides and Pre-Depends really belong here, but they're somewhat informative compared to the rest
                    "Provides": "Provides", "Pre-Depends": "pdep"}

# I don't think any official package tracker shows these, but I'm including them for
# completeness. That said, I don't know of any established abbreviations so I'm
# keeping them as-is.
if SHOW_EXTENDED_RELATIONS:
    DEPENDENCY_TYPES.update({"Conflicts": "Conflicts", "Breaks": "Breaks", "Replaces": "Replaces",
                             "Enhances": "Enhances", "Build-Conflicts": "Build-Conflicts",
                             "Build-Conflicts-Indep": "Build-Conflicts-Indep", "Built-Using": "Built-Using"})

def plist(dist):
    packagelist = []
    unique = set()
    snapshotregex = re.compile(SNAPSHOT_REGEX_BASE % dist)
    try:
        try:  # Try to find a snapshot matching the distribution
            snapshotname = [s for s in snapshotlist if snapshotregex.search(s)][-1]
        except IndexError:  # If that fails, just treat it as a repo
            print('Using packages in repo %r...' % dist)
            packages_raw = subprocess.check_output(("aptly", "repo", "show", "-with-packages", dist)).splitlines()
        else:
            print('Using packages in snapshot %r...' % snapshotname)
            packages_raw = subprocess.check_output(("aptly", "snapshot", "show", "-with-packages", snapshotname)).splitlines()
    except subprocess.CalledProcessError:  # It broke, whatever...
        return

    for line in packages_raw[packages_raw.index(b"Packages:"):]:
        # We can't get a raw list of packages, but all package entries are indented... Use that.
        if line.startswith(b" "):
            # Each package is given as a string in the format packagename_version_arch
            fullname = line.decode("utf-8").strip()
            name, version, arch = fullname.split("_")

            # Track a list of unique source packages
            if arch == "source":
                 unique.add(name)

            packagelist.append((name, version, arch, fullname))
    # Sort everything by package name
    packagelist.sort(key=lambda k: k[0])

    os.chdir(OUTDIR)
    with open('%s_list.html' % dist, 'w') as f:
        f.write("""<!DOCTYPE HTML>
<html>
<head><title>Package List for the Utopia Repository - {}</title>
<meta charset="UTF-8">
<meta name=viewport content="width=device-width">
{}
</head>
<body>
<a href="/">Back to root</a>
<br><br>
<table class="sortable">
<tr>
<th>Package Name</th>
<th>Version</th>
<th>Architectures</th>""".format(dist, EXTRA_STYLES))
        # Note: preserve this order when formatting the <td>'s later on, or the results
        # will be in the wrong column!
        if SHOW_CHANGELOGS:
            f.write("""<th>Changelog</th>""")
        if SHOW_VCS_LINKS:
            f.write("""<th>Vcs-Browser</th>""")
        if SHOW_DEPENDENCIES:
            f.write("""<th>Package Relations</th>""")
        f.write("""
</tr>
""")
        for p in packagelist:
            # If enabled, try to find a link to the file for the package given.
            if SHOW_POOL_LINKS or SHOW_CHANGELOGS or SHOW_DEPENDENCIES:
                #print("Finding links for %s" % str(p))
                name, version, arch, fullname = p
                download_link = arch

                poolresults = subprocess.check_output(("aptly", "package", "show", "-with-files", fullname))

                # First, locate the raw filename corresponding to the package we asked for.
                filename = ''
                changelog_path = ''
                vcs_link = ''
                relations = collections.OrderedDict()

                for line in poolresults.splitlines():
                    line = line.decode('utf-8')
                    fields = line.split()

                    if line.startswith('Vcs-Browser:'):
                        vcs_link = fields[1]

                    if line.startswith('Filename:'):
                        # .deb's get a fancy "Filename: hello_1.0.0-1_all.deb" line in aptly's output.
                        filename = fields[1]
                    if arch == 'source' and '.dsc' in line and len(fields) == 3:
                        # Source packages are listed as raw files in the pool though. Look for .dsc
                        # files in this case, usually in the line format
                        # 72c1479a7564c47cc2643336332c1e1d 711 utopia-defaults_2016.05.21+1.dsc
                        filename = fields[-1]
                    # Parse dependency lines
                    for deptype, depname in DEPENDENCY_TYPES.items():
                        if line.startswith(deptype + ':'):
                            relations[depname] = line.split(' ', 1)[-1]

                if filename and (SHOW_POOL_LINKS or SHOW_CHANGELOGS):
                    # Then, once we've found the filename, look it up in the pool/ tree we made
                    # earlier.
                    #print("Found filename %s for %s" % (filename, fullname))
                    for poolfile in poolobjects:
                        if poolfile.name == filename:
                            # Filename matched found, make the "arch" field a relative link to the path given.
                            location = poolfile.relative_to(OUTDIR)
                            download_link = '<a href="%s">%s</a>' % (location, arch)
                            if SHOW_CHANGELOGS and arch != 'source':  # XXX: there's no easy way to generate changelogs from sources
                                changelog_path = os.path.splitext(str(location))[0] + '.changelog'
                                if CHANGELOG_CACHE_DIR:
                                    cache_path = os.path.join(CHANGELOG_CACHE_DIR, os.path.basename(changelog_path))
                                    #print("    Caching changelog to %s" % cache_path)
                                else:
                                    cache_path = changelog_path

                                if not os.path.exists(changelog_path):
                                    # There's a new changelog file name for every version, so don't repeat generation
                                    # for versions that already have a changelog.

                                    full_path = str(poolfile.resolve())
                                    if os.path.getsize(full_path) > MAX_CHANGELOG_FILE_SIZE:
                                        print("    Skipping .deb %s; file size too large" % poolfile.name)
                                        break
                                    elif name.endswith(('-dbg', '-dbgsym')):
                                        print("    Skipping .deb %s; debug packages don't use changelogs" % poolfile.name)
                                        break

                                    if not os.path.exists(cache_path):
                                        # Cache doesn't exist, so make a new file.
                                        print("    Reading .deb %s" % poolfile.name)
                                        deb = debfile.DebFile(full_path)
                                        changelog = deb.changelog()
                                        if changelog:
                                            with open(cache_path, 'w') as changes_f:
                                                print("    Writing changelog for %s (%s) to %s" % (fullname, filename, changelog_path))
                                                try:
                                                    changelog.write_to_open_file(changes_f)
                                                except ValueError:  # Something went wrong, bleh.
                                                    traceback.print_exc()
                                                    continue

                                    if changelog_path != cache_path:
                                        print("    Linking cached changelog %s to %s" % (cache_path, changelog_path))
                                        try:
                                            os.link(cache_path, changelog_path)
                                        except OSError:
                                            traceback.print_exc()
                                            continue

                            #print("Found %s for %s" % (poolfile, fullname))
                            break

                f.write(("""<tr>
<td>{}</td>
<td>{}</td>
<td>{}</td>
""".format(name, version, download_link)))
                if SHOW_CHANGELOGS:
                    # Only fill in the changelog column if it is enabled, and the changelog exists.
                    if changelog_path and os.path.exists(changelog_path):
                        f.write("""<td><a href="{}">Changelog</a></td>""".format(changelog_path))
                    else:
                        f.write("""<td>N/A</td>""")
                if SHOW_VCS_LINKS:
                    if vcs_link:
                        f.write("""<td><a href="{0}">{0}</a>""".format(vcs_link))
                    else:
                        f.write("""<td>N/A</td>""")
                if SHOW_DEPENDENCIES:
                    text = ''
                    for depname, data in relations.items():
                        text += """<span class="dependency deptype-{0}">{0}</span>: {1}<br>""".format(depname, data)
                    f.write("""<td>{}</td>""".format(text))
                f.write("""
</tr>
""")
        f.write("""</table>
<p><b>Total items:</b> {} ({} unique source packages)</p>
<p>Last updated {}</p>
</body></html>""".format(len(packagelist), len(unique), time.strftime("%I:%M:%S %p, %b %d %Y +0000", time.gmtime())))

if __name__ == "__main__":
    try:
        repolist = [sys.argv[1]]
    except IndexError:
        pass
    for dist in repolist:
        print('Processing package lists for %r.' % dist)
        plist(dist)
