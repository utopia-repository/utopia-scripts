#!/usr/bin/env python3
"""
Runs uscan on all non-native packages in a repository.
"""
import io
import os
import shutil
import subprocess
import sys
import tarfile
import traceback
import xml.etree.ElementTree

if not shutil.which('uscan'):
    print('ERROR: uscan binary not found, aborting.')
    sys.exit(1)

import apt_pkg
apt_pkg.init()

try:
    from aptlylist_conf import EXTRA_STYLES
except ImportError:
    EXTRA_STYLES = ''

try:
    TARGET = sys.argv[1]
    TO_PROCESS_INFILE = sys.argv[2]
    OUTFILE = sys.argv[3]
except IndexError:
    print('Needs three arguments: path to repository pool/, path to list of sources to search for (newline-separated), output filename')
    sys.exit(1)

FILES = {}
_USCAN_WATCH_FILE_NOT_FOUND = "watch file not found"
_USCAN_FAILED = "failed to get status"
_USCAN_PROBABLY_NATIVE = "N/A package is native"
_USCAN_FORMAT = {
    "newer package available": "💡",
    "only older package available": "⁉️",
    "up to date": "✔️",
    _USCAN_FAILED: "❌",
    _USCAN_WATCH_FILE_NOT_FOUND: "🤷",
    _USCAN_PROBABLY_NATIVE: "↷",
}

def _populate_files():
    for root, dirs, files in os.walk(TARGET):
        for fname in files:
            # Look for all files named debian.tar.(xz|gz|bz2)
            if '.debian.tar.' in fname:
                package = fname.split('.debian.tar.', 1)[0]
                package, version = package.split('_', 2)
                # Try to find the newest package to extract debian/watch from
                # XXX: epochs not handled due to them not being in filenames
                if package not in FILES or apt_pkg.version_compare(version, FILES[package][0]) >= 1:
                    FILES[package] = (version, os.path.join(root, fname))
                    #print('Saved', package, 'as', FILES[package])

def _parse_dehs(data):
    """
    Parses dehs data from uscan and returns a tuple if successful:
        (status, upstream version, upstream url)
    """
    root = xml.etree.ElementTree.fromstring(data)
    status = root.find('status').text
    upstream_ver = root.find('upstream-version').text
    upstream_url = root.find('upstream-url').text
    print("Got uscan data %r, %r, %r" % (status, upstream_ver, upstream_url))
    return (status, upstream_ver, upstream_url)

def _get_uscan_data(pkgname, uversion, archive):
    try:
        with tarfile.open(archive, 'r') as tar_f:
            try:
                watchfile = tar_f.extractfile("debian/watch")
            except KeyError:
                return False
            if watchfile is None:
                return False

            print("Checking uscan on package %s" % archive)
            proc = subprocess.Popen([
                'uscan', '--dehs',
                '--package', pkgname,
                '--upstream-version', uversion,
                #'--verbose',
                '--watchfile', '-'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            uscan_dehs, _ = proc.communicate(watchfile.read())
            watchfile.close()

            try:
                return _parse_dehs(uscan_dehs.decode('utf-8'))
            except:
                print("Failed to get uscan info:")
                traceback.print_exc()
    except (tarfile.TarError, OSError):
        print("Failed to extract tarball %s" % archive)
        traceback.print_exc()

def main():
    _populate_files()

    f = open(OUTFILE + '.tmp', 'w')
    f.write("""<!DOCTYPE HTML>
<html>
<head><title>Watch - Utopia Repository</title>
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
<th title="Best guess, excluding epochs" class="tooltip">My Version</th>
<th>Watch Status</th>""".format(EXTRA_STYLES))

    with open(TO_PROCESS_INFILE) as to_process_f:
        to_process = [s.strip() for s in to_process_f]

    for package in to_process:
        uscan_info = False
        version = "N/A"
        upstream = url = ''
        if package in FILES:
            version, tarball = FILES[package]
            # Strip out Debian revision
            uversion = version.rsplit('-', 1)[0]
            uscan_info = _get_uscan_data(package, uversion, tarball)

            if uscan_info:
                status, upstream, url = uscan_info
                status = status.strip()
            elif uscan_info is False:  # watch file missing
                status = _USCAN_WATCH_FILE_NOT_FOUND
            else:  # Wasn't able to get anything
                status = _USCAN_FAILED
        else:
            # Likely a native package, no matching .debian.tar.* found
            status = _USCAN_PROBABLY_NATIVE

        # Prettify uscan format when applicable
        status_symbol = _USCAN_FORMAT.get(status)
        if status_symbol:
            status = '{} {}'.format(status_symbol, status)

        f.write("""
<tr>
    <td>{}</td>
    <td>{}</td>""".format(package, version))
        if url:
            f.write("""<td>{0}<br>upstream: <a href="{2}">{1}</a></td>""".format(status, upstream, url))
        else:
            f.write("""<td>{0}</td>""".format(status))

        f.write("""</tr>""")

    f.write("""</table>
</body>
</html>""")
    f.close()
    os.rename(OUTFILE + '.tmp', OUTFILE)

if __name__ == '__main__':
    main()
