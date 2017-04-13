#!/usr/bin/env python3
"""
Installability checker for Apt repositories, using dose-debcheck as a backend.

By default, this downloads Packages files for the relevant distributions into a temporary folder (as Packages_REPO_DIST_SUITE_ARCH) and outputs results as Installcheck_REPO_DIST_SUITE_ARCH.txt in the current folder.
"""

### BEGIN CONFIGURATION

# A list of known repositories.
REPOS = {'debian': 'http://httpredir.debian.org/debian',
         'urepo': 'https://packages.overdrivenetworks.com'}

# A list of architectures to test against.
TARGET_ARCHS = ['amd64', 'i386']

# Map (distribution, suite) pairs to test to a list of (repo, distribution, suite) pairs to depend on.
TARGET_DISTS = {
    ('urepo', 'sid', 'main'): [('debian', 'sid', 'main')],
    ('urepo', 'sid', 'imports'): [('debian', 'sid', 'main'),
                                  ('debian', 'sid', 'contrib'),
                                  ('debian', 'sid', 'non-free'),
                                  ('urepo', 'sid', 'main')],
    ('urepo', 'sid', 'forks'): [('debian', 'sid', 'main'),
                                 ('urepo', 'sid', 'main')],
}

### END CONFIGURATION

import urllib.request
import os
import gzip
import subprocess
import sys
import tempfile
import argparse

PACKAGES_FILES = {}

def download_packages_file(repo, dist, suite, arch, skip_download=False):
    """
    Gets the Packages file given the repository, distribution, suite, and
    architecture.
    """
    # http://cdn-fastly.deb.debian.org/debian/dists/sid/main/binary-amd64/
    link = '%s/dists/%s/%s/binary-%s/Packages.gz' % (REPOS[repo], dist, suite, arch)
    filename = 'Packages_%s_%s_%s_%s' % (repo, dist, suite, arch)

    if not skip_download:
        print('Getting packages link %s' % link)
        # TODO: we should probably make sure the relevant Packages files actually exist...
        request = urllib.request.Request(link, headers={'User-Agent': "Mozilla/5.0 (compatible)"})
        data = urllib.request.urlopen(request).read()
        extracted_data = gzip.decompress(data)

        with open(filename, 'wb') as f:
            f.write(extracted_data)
    else:
        print('Reusing packages file %s' % filename)

    return filename

def test_dist(repo, dist, suite, arch, outfile=None):
    """
    Runs dose-debcheck on a repo, dist, suite, and arch pair.
    """

    deps = TARGET_DISTS[(repo, dist, suite)]
    # What we what to run is:
    #  dose-debcheck -fe Packages_of_target --bg Packages_of_dependency_1
    #  --bg Packages_of_dependency_2 ...
    cmd = ['dose-debcheck', '-fe', PACKAGES_FILES[(repo, dist, suite, arch)]]
    for dep in deps:
        dep = (dep[0], dep[1], dep[2], arch)
        cmd += ['--bg', PACKAGES_FILES[dep]]

    print('Running command', cmd)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    if outfile:
        outfile.write('Results for %s, %s, %s:\n' % (repo, dist, suite))

    # Read stdout as dose-debcheck runs instead of only returning results at the end.
    for line in process.stdout:
        line = line.decode()
        print(line, end='')
        if outfile:
            outfile.write(line)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-t", "--tempdir", help="sets the temporary directory to download Packages files into", type=str, default=tempfile.mkdtemp())
    parser.add_argument("-o", "--outdir", help="sets the output directory to write results to", type=str, default=os.getcwd())
    parser.add_argument("-s", "--skip-download", help="skips downloading new Packages file (most useful with a custom tempdir)", action='store_true')
    args = parser.parse_args()

    print('Using %s as tempdir' % args.tempdir)
    print('Using %s as outdir' % args.outdir)

    os.chdir(args.tempdir)

    # Iterate over all target dists and their dependencies, and get their package files
    for arch in TARGET_ARCHS:
        for target in TARGET_DISTS:
            # Store these as a 4-item tuple: repo name, distribution, suite, and architecture
            repoidx = (target[0], target[1], target[2], arch)
            if repoidx not in PACKAGES_FILES:
                # If we already know a repository's packages file, don't redownload it
                PACKAGES_FILES[repoidx] = download_packages_file(*repoidx, skip_download=args.skip_download)

            for dependency in TARGET_DISTS[target]:
                repoidx = (dependency[0], dependency[1], dependency[2], arch)
                if repoidx not in PACKAGES_FILES:
                    PACKAGES_FILES[repoidx] = download_packages_file(*repoidx, skip_download=args.skip_download)
    print()

    for arch in TARGET_ARCHS:
        for target in TARGET_DISTS:
            outfile = 'Installcheck_%s_%s_%s_%s.txt' % (target[0], target[1], target[2], arch)
            outfile = os.path.join(args.outdir, outfile)
            print('Writing installability check results for target %s to %s' % (target, outfile))
            with open(outfile, 'w') as f:
                test_dist(target[0], target[1], target[2], arch, outfile=f)

