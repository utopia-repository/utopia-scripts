#!/bin/bash
OUTDIR="packages.overdrivenetworks.com.mirror"

rsync --verbose -a --progress --bwlimit=10100 pub@45.79.66.40::packages "$OUTDIR" --delete-after --exclude .lastsync --password-file ~/.rsync.pwd

echo ""
echo "Writing last synced time to $OUTDIR/.lastsync"
date -Ru | tee $OUTDIR/.lastsync
