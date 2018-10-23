#!/usr/bin/env python3
"""
Snapshot update announcer for aptly servers: when ran on an interval, this
script fetches all published snapshots from aptly (via a subprocess), saves
them, and announces any changes since the last execution to a FIFO pipe.

Some FIFO-based chat clients include http://tools.suckless.org/ii/ for IRC
and https://github.com/contyk/jj for Jabber/XMPP.
"""

import re
import subprocess
import json
import pprint
import os
import os.path

### BEGIN CONFIGURATION

# Determines where the snapshot list from the last execution should be stored.
FILENAME = 'aptly-snapshots.list'

# Determines the folder where diffs should be created.
OUTDIR = '/srv/aptly/public/sndiff'

# FIFO pipe to announce to
ANNOUNCE_DEST = os.path.expanduser('~/ii/localhost/#dev/in')

# Formats the text when using FIFO announce
# 0 = target dist, 1 = old snapshot, 2 = new snapshot, 3 = snapshot diff filename
ANNOUNCE_FORMAT = 'New packages released for {0}: {1} -> {2} https://deb.utopia-repository.org/sndiff/{3}'

# Sets the format for diff formats. 0 = target dist, 1 = old snapshot name, 2 = new snapshot name
DIFF_FILENAME_FORMAT = '{1}_{2}.txt'

### END CONFIGURATION

os.makedirs(OUTDIR, exist_ok=True)
text = subprocess.check_output(['aptly', 'publish', 'list']).decode()
try:
    with open(FILENAME) as f:
        ORIG_SNAPSHOT_LIST = json.load(f)
    print('Got existing snapshot list:')
    pprint.pprint(ORIG_SNAPSHOT_LIST)
except (ValueError, OSError):
    print('Failed to open %s, ignoring' % FILENAME)
    ORIG_SNAPSHOT_LIST = {}

SNAPSHOT_LIST = {}

for line in text.splitlines():
    line = line.strip()
    match = re.match(r"""^\* (.*?) \[(.*?)\] publishes (\{.*?\}[,]?)+$""", line)
    if match:
        target, archs, raw_snapshots = match.groups()
        print('Publish target %s' % target)
        print('    archs: %s' % archs)
        print('    snapshots: %s' % raw_snapshots)
        snapshots = re.findall(r"""\{(.*?)\: \[(.*?)\]""", raw_snapshots)
        print('    filtered snapshots: %s' % snapshots)
        for snapshot_pair in snapshots:
            # JSON doesn't allow lists as indices, so we lazily join the dist and component here...
            snid = '%s///%s' % (target, snapshot_pair[0])
            SNAPSHOT_LIST[snid] = snapshot = snapshot_pair[1]

            old_snapshot = ORIG_SNAPSHOT_LIST.get(snid)
            if snapshot != old_snapshot:
                if not old_snapshot:
                    print('Skipping first announce for repository %s' % snapshot)
                    continue
                print('NEW snapshot for %s: %s -> %s' % (target, old_snapshot, snapshot))
                diff = subprocess.check_output(['aptly', 'snapshot', 'diff', old_snapshot, snapshot]).decode()

                diff_filename = DIFF_FILENAME_FORMAT.format(target, old_snapshot, snapshot)
                diff_outpath = os.path.join(OUTDIR, diff_filename)
                print('Writing diff to %s:' % diff_outpath)
                print(diff)
                with open(diff_outpath, 'w') as diff_f:
                    diff_f.write('Changes from %s to %s:\n' % (old_snapshot, snapshot))
                    diff_f.write(diff)
                with open(ANNOUNCE_DEST, 'w') as fifo_f:
                    fifo_f.write(ANNOUNCE_FORMAT.format(target.lstrip('/.'), old_snapshot, snapshot, diff_filename))
                    fifo_f.write('\n')

print()
print('Writing publish list to %s:' % FILENAME)
pprint.pprint(SNAPSHOT_LIST)
with open(FILENAME, 'w') as f:
    json.dump(SNAPSHOT_LIST, f, indent=4)
