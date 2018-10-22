#!/usr/bin/env python3
"""
Installability checker for Apt repositories, using dose-debcheck as a backend.

By default, this downloads Packages files for the relevant distributions into a temporary folder (as Packages_REPO_DIST_SUITE_ARCH) and outputs results as Installcheck_REPO_DIST_SUITE_ARCH.txt in the current folder.
"""
from __future__ import print_function

### BEGIN CONFIGURATION

# A list of known repositories.
REPOS = {'debian': 'http://httpredir.debian.org/debian',
         'urepo': 'https://deb.utopia-repository.org',
         'urepo-nightlies': 'https://ni.deb.utopia-repository.org',
         'urepo-test-ubuntu-stable': 'https://deb.utopia-repository.org',
         'urepo-test-ubuntu-devel': 'https://deb.utopia-repository.org',
         'ubuntu': 'http://archive.ubuntu.com/ubuntu'}

# A list of architectures to test against.
TARGET_ARCHS = ['amd64', 'i386', 'arm64']

# Map (distribution, suite) pairs to test to a list of (repo, distribution, suite) pairs to depend on.
TARGET_DISTS = {
    ('urepo', 'sid', 'main'): [('debian', 'sid', 'main')],
    ('urepo', 'sid', 'imports'): [('debian', 'sid', 'main'),
                                  ('debian', 'sid', 'contrib'),
                                  ('debian', 'sid', 'non-free'),
                                  ('urepo', 'sid', 'main')],
    ('urepo', 'sid', 'forks'): [('debian', 'sid', 'main'),
                                ('urepo', 'sid', 'main')],
    ('urepo-nightlies', 'sid-nightlies', 'main'): [('debian', 'sid', 'main'),
                                                   ('urepo', 'sid', 'main')],

    ('urepo', 'stretch', 'main'): [('debian', 'stretch', 'main'),
                                   ('debian', 'stretch-backports', 'main'),
                                   ('urepo', 'stretch', 'imports'),
                                  ],
    ('urepo', 'stretch', 'imports'): [('debian', 'stretch', 'main'),
                                      ('debian', 'stretch', 'contrib'),
                                      ('debian', 'stretch', 'non-free'),
                                      ('urepo', 'stretch', 'main'),
                                     ],
    ('urepo', 'stretch', 'forks'): [('debian', 'stretch', 'main'),
                                    ('urepo', 'stretch', 'main'),
                                   ],

    ('urepo', 'xenial', 'main'): [('ubuntu', 'xenial', 'main'),
                                  ('ubuntu', 'xenial', 'universe')],

    ('urepo', 'bionic', 'main'): [('ubuntu', 'bionic', 'main'),
                                  ('ubuntu', 'bionic', 'universe')],
    ('urepo', 'bionic', 'imports'): [('ubuntu', 'bionic', 'main'),
                                      ('ubuntu', 'bionic', 'universe'),
                                      ('ubuntu', 'bionic', 'restricted'),
                                      ('ubuntu', 'bionic', 'multiverse'),
                                      ('urepo', 'bionic', 'main')],
    ('urepo', 'bionic', 'forks'): [('ubuntu', 'bionic', 'main'),
                                   ('urepo', 'bionic', 'main')],
    #('urepo-test-ubuntu-stable', 'sid', 'main'): [('ubuntu', 'bionic', 'main'),
    #                                              ('ubuntu', 'bionic', 'universe')],
    #('urepo-test-ubuntu-stable', 'sid', 'imports'): [('ubuntu', 'bionic', 'main'),
    #                                                 ('ubuntu', 'bionic', 'universe'),
    #                                                 ('ubuntu', 'bionic', 'restricted'),
    #                                                 ('ubuntu', 'bionic', 'multiverse')],
    #('urepo-test-ubuntu-devel', 'sid', 'main'): [('ubuntu', 'devel', 'main'),
    #                                             ('ubuntu', 'devel', 'universe')],
}

### END CONFIGURATION

import urllib.request
import os
import gzip
import subprocess
import sys
import tempfile
import argparse
import multiprocessing
import traceback
import shutil

manager = multiprocessing.Manager()
PACKAGES_FILES = manager.dict()

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
        try:
            data = urllib.request.urlopen(request).read()
        except OSError:
            traceback.print_exc()
            print('Failed to download %s, skipping the combination (%r, %r, %r, %r)' % (link, repo, dist, suite, arch))
            return
        extracted_data = gzip.decompress(data)

        with open(filename, 'wb') as f:
            f.write(extracted_data)
    else:
        if os.path.isfile(filename):
            print('Reusing Packages file %s' % filename)
        else:
            print('Missing Packages file %s; some tests may be skipped!' % filename)
            return

    global PACKAGES_FILES
    PACKAGES_FILES[(repo, dist, suite, arch)] = filename
    return filename

def test_dist(repo, dist, suite, arch, outfilename=None):
    """
    Runs dose-debcheck on a repo, dist, suite, and arch pair.
    """
    if (repo, dist, suite, arch) not in PACKAGES_FILES:  # Unavailable combination
        print("Skipping dist (%r, %r, %r, %r) as it is not available" % (repo, dist, suite, arch))
        return

    deps = TARGET_DISTS[(repo, dist, suite)]
    # What we what to run is:
    #  dose-debcheck -fe Packages_of_target --bg Packages_of_dependency_1
    #  --bg Packages_of_dependency_2 ...
    cmd = ['dose-debcheck', '-fe', PACKAGES_FILES[(repo, dist, suite, arch)]]
    for dep_target in deps:
        dep = (dep_target[0], dep_target[1], dep_target[2], arch)

        if dep not in PACKAGES_FILES:  # Unavailable dependency
            print("Skipping dist (%r, %r, %r, %r) as dependency %r not available" % (repo, dist, suite, arch, dep))
            return
        cmd += ['--bg', PACKAGES_FILES[dep]]

    print('Running command', cmd)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    # Read stdout as dose-debcheck runs instead of only returning results at the end.
    lines = []  # XXX: is storing the output text this way this efficient?
    for line in process.stdout:
        line = line.decode()
        print(line, end='')
        lines.append(line)

    process.wait()
    print('process returncode: %s' % process.returncode)
    if outfilename is not None and process.returncode != 0:
        with open(outfilename, 'w') as outfile:
            # Only write reports for combinations that fail testing.
            outfile.write('Results for %s, %s, %s:\n' % (repo, dist, suite))
            outfile.writelines(lines)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-t", "--tempdir", help="sets the temporary directory to download Packages files into", type=str, default=tempfile.mkdtemp())
    parser.add_argument("-o", "--outdir", help="sets the output directory to write results to", type=str, default=os.getcwd())
    parser.add_argument("-s", "--skip-download", help="skips downloading new Packages file (most useful with a custom tempdir)", action='store_true')
    parser.add_argument("-p", "--processes", help="amount of processes to use (defaults to amount of CPU cores)", type=int, default=os.cpu_count() or 1)
    args = parser.parse_args()

    if not shutil.which('dose-debcheck'):
        raise OSError("Could not find 'dose-debcheck' in the PATH!")

    print('Using %s as tempdir' % args.tempdir)
    print('Using %s as outdir' % args.outdir)

    os.chdir(args.tempdir)

    needed_packages = set()

    for arch in TARGET_ARCHS:
        for target in TARGET_DISTS:
            # Store these as a 4-item tuple: repo name, distribution, suite, and architecture
            repoidx = (target[0], target[1], target[2], arch)
            needed_packages.add(repoidx)

            # Process this target's dependencies as well
            for dependency in TARGET_DISTS[target]:
                repoidx = (dependency[0], dependency[1], dependency[2], arch)
                needed_packages.add(repoidx)

    def download_wrapper(pkg):
        print('Running download_packages_file in Process %s' % multiprocessing.current_process())
        download_packages_file(*pkg, skip_download=args.skip_download)

    def test_dist_wrapper(target, outfile=None, **kwargs):
        outfile = 'Installcheck_%s_%s_%s_%s.txt' % target
        outfile = os.path.join(args.outdir, outfile)

        print('Writing installability check results for target %s to %s' % (target, outfile))
        print('Running test_dist in Process %s' % multiprocessing.current_process())
        test_dist(*target, outfilename=outfile)

    with multiprocessing.Pool(args.processes) as pool:
        # Download all the Packages files we need in separate worker processes, to speed up the process.
        pool.map(download_wrapper, needed_packages)

        # Build a list of targets to run
        real_targets = []
        for arch in TARGET_ARCHS:
            for target in TARGET_DISTS:
                real_targets.append((target[0], target[1], target[2], arch))

        # Run them!
        pool.map(test_dist_wrapper, real_targets)
