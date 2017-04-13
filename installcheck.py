#!/usr/bin/env python3
"""
Installability checker for Apt repositories, using dose-debcheck as a backend.

By default, this downloads Packages files for the relevant distributions into a temporary folder (as Packages_REPO_DIST_SUITE_ARCH) and outputs results as Installcheck_REPO_DIST_SUITE_ARCH.txt in the current folder.
"""

### BEGIN CONFIGURATION

# A list of known repositories.
REPOS = {'debian': 'http://httpredir.debian.org/debian',
         'urepo': 'https://packages.overdrivenetworks.com',
         'ubuntu': 'http://archive.ubuntu.com/ubuntu'}

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
    ('urepo', 'sid-nightlies', 'main'): [('debian', 'sid', 'main'),
                                    ('urepo', 'sid', 'main')],
    ('urepo', 'jessie', 'main'): [('debian', 'jessie', 'main'),
                                  #('debian', 'jessie-backports', 'main'),
                                  ('urepo', 'jessie', 'imports'),
                                  ],
    ('urepo', 'jessie', 'imports'): [('debian', 'jessie', 'main'),
                                     ('debian', 'jessie', 'contrib'),
                                     ('debian', 'jessie', 'non-free'),
                                     ('urepo', 'jessie', 'main'),
                                     ],
    ('urepo', 'jessie-backports', 'main'): [('debian', 'jessie-backports', 'main'),
                                            ('debian', 'jessie', 'main')],
    ('urepo', 'jessie-backports', 'testing'): [('debian', 'jessie-backports', 'main'),
                                               ('urepo', 'jessie-backports', 'main'),
                                               ('debian', 'jessie', 'main')],
    ('urepo', 'xenial', 'main'): [('ubuntu', 'xenial', 'main'),
                                  ('ubuntu', 'xenial', 'universe')],
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
        data = urllib.request.urlopen(request).read()
        extracted_data = gzip.decompress(data)

        with open(filename, 'wb') as f:
            f.write(extracted_data)
    else:
        print('Reusing packages file %s' % filename)

    global PACKAGES_FILES
    PACKAGES_FILES[(repo, dist, suite, arch)] = filename
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
    parser.add_argument("-p", "--processes", help="amount of processes to use (defaults to amount of CPU cores)", type=int, default=os.cpu_count() or 1)
    args = parser.parse_args()

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
        outfile = 'Installcheck_%s_%s_%s_%s.txt' % (target[0], target[1], target[2], arch)
        outfile = os.path.join(args.outdir, outfile)

        print('Writing installability check results for target %s to %s' % (target, outfile))
        with open(outfile, 'w') as f:
            print('Running test_dist in Process %s' % multiprocessing.current_process())
            test_dist(*target, outfile=f)

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
