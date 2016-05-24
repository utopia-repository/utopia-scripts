#!/usr/bin/env python3
import time
import subprocess
import sys
import shutil
import os
import re

### BEGIN CONFIGURATION VARIABLES ###
outdir = "/srv/aptly/public"
extradists = ["sid-imports"]

# REGEX to look for snapshots for the distribution we're looking up. Defaults to ${dist}-YYYY-MM-DD.
# If this regex doesn't match a certain distribution, it is treated as its own repository in lookup.
snapshotregex_base = r'^%s-\d{4}-\d{2}-\d{2}'  # First %s is the distribution name

### END CONFIGURATION VARIABLES ###

if not shutil.which('aptly'):
    print('Error: aptly not found in path!')
    sys.exit(1)

print('Output directory set to: %s' % outdir)
repolist = subprocess.check_output(("aptly", "repo", "list", "-raw")).decode('utf-8').splitlines()
mirrorlist = subprocess.check_output(("aptly", "mirror", "list", "-raw")).decode('utf-8').splitlines()
repolist += mirrorlist
repolist += extradists
snapshotlist = subprocess.check_output(("aptly", "snapshot", "list", "-raw")).decode('utf-8').splitlines()

def plist(dist):
    packagelist = []
    unique = set()
    snapshotregex = re.compile(snapshotregex_base % dist)
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
    for line in packages_raw:
        # We can't get a raw list of packages, but all package entries are indented... Use that.
        if line.startswith(b" "):
            # s is a string in the format packagename_version_arch
            name, version, arch = line.decode("utf-8").strip().split("_")

            # Track a list of unique source packages
            if arch == "source":
                 unique.add(name)

            packagelist.append((name, version, arch))
    # Sort everything by package name
    packagelist.sort(key=lambda k: k[0])

    os.chdir(outdir)
    with open('%s_list.html' % dist, 'w') as f:
        f.write("""<!DOCTYPE HTML>
<html>
<head><title>Package List for the Utopia Repository - {}</title>
<meta charset="UTF-8">
<meta name=viewport content="width=device-width">
<link rel="stylesheet" type="text/css" href="gstyle.css">
</head>
<body>
<a href="javascript:history.back()">Go back</a>
<br><br>
<table>
<tr>
<th>Package Name</th>
<th>Version</th>
<th>Architectures</th>
</tr>""".format(dist))
        for p in packagelist:
            f.write(("""<tr><td>{}</td><td>{}</td><td>{}</td></tr>"""
                .format(*p)))
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
