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
import html

try:
    from aptlylist_conf import *
except ImportError:
    print("Error: Could not load aptlylist_conf.py; does that file exist?", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)

print('Output directory set to: %s' % OUTDIR)

if SHOW_CHANGELOGS:
    from debian import changelog, debfile
    if not CHANGELOG_TARGET_DIR:
        print("Error: SHOW_CHANGELOGS is true but no CHANGELOG_TARGET_DIR set", file=sys.stderr)
        sys.exit(1)
    else:
        print("Changelog directory set to: %s" % CHANGELOG_TARGET_DIR)

if not shutil.which('aptly'):
    print('Error: aptly not found in path!')
    sys.exit(1)

snapshotlist = subprocess.check_output(("aptly", "snapshot", "list", "-raw")).decode('utf-8').splitlines()

if SHOW_POOL_LINKS or SHOW_CHANGELOGS:
    import pathlib
    # Enumerate all objects in pool/. XXX: ugly globs......
    poolobjects = collections.defaultdict(set)
    for repofile in pathlib.Path(OUTDIR).glob('pool/*/*/*/*.d??'):
        # Store packages by name, not by name+version because epochs are not written into the filename!
        pkgname = repofile.name.split('_')[0]
        poolobjects[pkgname].add(repofile)

    if not os.path.exists(CHANGELOG_TARGET_DIR):
        print("Creating changelog dir %s" % CHANGELOG_TARGET_DIR)
        os.mkdir(CHANGELOG_TARGET_DIR)

DEPENDENCY_TYPES = ['Build-Depends', 'Build-Depends-Indep', 'Depends', 'Enhances', 'Recommends', 'Suggests',
# Not sure whether Provides and Pre-Depends really belong here, but they're somewhat informative compared to the rest
                    'Provides', 'Pre-Depends']

# I don't think any official package tracker shows these, but I'm including them for
# completeness. That said, I don't know of any established abbreviations so I'm
# keeping them as-is.
if SHOW_EXTENDED_RELATIONS:
    DEPENDENCY_TYPES += ["Conflicts", "Breaks", "Replaces", "Build-Conflicts",
                         "Build-Conflicts-Indep", "Built-Using"]

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
    with open('%s_sources.txt' % dist, 'w') as sources_f:
        sources_f.write('\n'.join(sorted(unique)))

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
            short_desc = ''

            # If enabled, try to find a link to the file for the package given.
            # XXX: is all this conditional stuff needed or should we make the 'package show' call implicit?
            if SHOW_POOL_LINKS or SHOW_CHANGELOGS or SHOW_DEPENDENCIES or SHOW_DESCRIPTIONS:
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

                    if line.startswith('Description:'):
                        short_desc = line.split(' ', 1)[-1]

                    # Parse dependency lines
                    for deptype in DEPENDENCY_TYPES:
                        if line.startswith(deptype + ':'):
                            relations[deptype] = line.split(' ', 1)[-1]

                if filename and (SHOW_POOL_LINKS or SHOW_CHANGELOGS):
                    # Then, once we've found the filename, look it up in the pool/ tree we made
                    # earlier.
                    #print("Found filename %s for %s" % (filename, fullname))
                    for poolfile in poolobjects[name]:
                        if poolfile.name == filename:
                            # Filename matched found, make the "arch" field a relative link to the path given.
                            location = poolfile.relative_to(OUTDIR)
                            download_link = '<a href="%s">%s</a>' % (location, arch)
                            if SHOW_CHANGELOGS and arch != 'source':  # XXX: there's no easy way to generate changelogs from sources
                                changelog_path = os.path.join(CHANGELOG_TARGET_DIR, '%s_%s.changelog' % (name, version))

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

                                    # Cached changelog doesn't exist, so make a new file.
                                    print("    Reading .deb %s" % full_path)
                                    deb = debfile.DebFile(full_path)
                                    changelog = deb.changelog()
                                    if changelog:
                                        with open(changelog_path, 'w') as changes_f:
                                            print("    Writing changelog for %s (%s) to %s" % (fullname, filename, changelog_path))
                                            try:
                                                changelog.write_to_open_file(changes_f)
                                            except ValueError:  # Something went wrong, bleh.
                                                traceback.print_exc()
                                                continue
                                    else:
                                        print("    Changelog generation FAILED for %s (deb.changelog() is empty?)" % fullname)
                                        continue

                            #print("Found %s for %s" % (poolfile, fullname))
                            break
                name_extended = name
                if short_desc and SHOW_DESCRIPTIONS:
                    # Format the name in a tooltip span if a description is available.
                    name_extended = """<span title="{0} - {1}" class="tooltip">{0}</span>""".format(name, html.escape(short_desc))

                f.write(("""<tr id="{0}_{3}">
<td>{4}</td>
<td>{1}</td>
<td>{2}</td>
""".format(name, version, download_link, html.escape(arch), name_extended)))
                if SHOW_CHANGELOGS:
                    # Only fill in the changelog column if it is enabled, and the changelog exists.
                    if changelog_path and os.path.exists(changelog_path):
                        f.write("""<td><a href="{}">Changelog</a></td>""".format(os.path.relpath(changelog_path, OUTDIR)))
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
                        text += """<span class="dependency deptype-{2}">{0}</span>: {1}<br>""".format(depname, data, depname.lower())
                    f.write("""<td>{}</td>""".format(text))
                f.write("""
</tr>
""")
        f.write("""</table>
<p><b>Total items:</b> {} ({} unique source packages)</p>
<p>Last updated {}</p>
</body></html>""".format(len(packagelist), len(unique), time.strftime("%I:%M:%S %p, %b %d %Y +0000", time.gmtime())))

if __name__ == "__main__":
    repolist = sys.argv[1:] or TARGET_DISTS
    print('Got target dists: %s' % repolist)
    for dist in repolist:
        print('Processing package lists for %r.' % dist)
        plist(dist)
