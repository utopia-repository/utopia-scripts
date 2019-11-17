#!/usr/bin/env python3
import sys
import subprocess
import pipes
from collections import defaultdict
import re
import time

def _error():
    print("error: unknown command, valid commands are 'getdup', 'msnapshot',"
          " 'refreshmirrors', 'purge', 'rsnapshot'")
    sys.exit(1)

def getdups(reponame):
    if reponame not in repos:
        print("error: repo '%s' does not exist!" % reponame)
        sys.exit(2)
    else:
        print('checking duplicates for repo %s...' % reponame)
        showpackages = subprocess.check_output(['aptly', 'repo', 'show', '-with-packages', reponame]).decode('utf-8').split("\n")
        uniqPackages = defaultdict(set)
        for p in showpackages:
            p = p.split("_")
            if len(p) == 3:
                packageName, version = p[0].strip(), p[1]
                uniqPackages[packageName].add(version)
        for p, v in uniqPackages.items():
            if len(v) > 1:
                print('Duplicate package: %s (%s)' % (p, ', '.join(v)))

def purge(reponame, packages):
    if reponame not in repos:
        print("error: repo '%s' does not exist!" % reponame)
        sys.exit(2)
    s = ['{0} | $Source ({0})'.format(p) for p in packages]
    s = ' | '.join(s)
    if s:
        sys.stdout.write(subprocess.check_output(['aptly', 'repo', 'remove', reponame, s]).decode('utf-8'))
    else:
        print('no matching packages')
        sys.exit(3)

date = time.strftime('%Y-%m-%d')
def _get_snapshot_name(src):
    snapshot_name = base_snapshot_name = '%s-%s' % (src, date)
    c = 0
    # Increment to reponame-date+X on snapshot name collision
    while snapshot_name in existing_snapshots:
        c += 1
        snapshot_name = "%s+%s" % (base_snapshot_name, c)
    return snapshot_name

try:
    command = sys.argv[1].lower()
except IndexError:
    _error()
params = sys.argv[2:]
repos = subprocess.check_output(['aptly', 'repo', 'list', '-raw']).decode('utf-8').split('\n')[:-1]
mirrors = subprocess.check_output(['aptly', 'mirror', 'list', '-raw']).decode('utf-8').split('\n')[:-1]

existing_snapshots = subprocess.check_output(['aptly', 'snapshot', 'list', '-raw']).decode('utf-8').splitlines()

if command == 'getdup':
    if len(sys.argv) < 3:
        print('error: needs repo name!')
        sys.exit(2)
    getdups(params[0])
elif command == 'msnapshot':
    mirrors = params or mirrors
    for mir in mirrors:
        snapshot_name = base_snapshot_name = '%s-%s' % (repo, date)
        sys.stdout.write(subprocess.check_output(['aptly', 'snapshot', 'create', _get_snapshot_name(mir), 'from', 'mirror', mir]).decode('utf-8'))

elif command == 'rsnapshot':
    repos = params or repos
    for repo in repos:
        sys.stdout.write(subprocess.check_output(['aptly', 'snapshot', 'create', _get_snapshot_name(repo), 'from', 'repo', repo]).decode('utf-8'))

elif command == 'refreshmirrors':
    for m in mirrors:
        sys.stdout.write(subprocess.check_output(['aptly', 'mirror', 'update', m]).decode('utf-8'))
elif command == 'purge':
    if len(sys.argv) < 3:
        print('error: needs repo name!')
        sys.exit(2)
    purge(params[0], params[1:])
else:
    _error()
