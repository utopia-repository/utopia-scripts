#!/bin/bash
###
# ii wrapper for Utopia Repository update announcements.
# Copyright (c) 2018 James Lu <james@overdrivenetworks.com>
###
II_PATH="${HOME}/ii"

NICK="utopia-announcer"
TARGET="localhost"   # For use with stunnel
PORT="16667"
CHANNEL="#dev"
REALNAME="Utopia Repository Updates Announcer"

echo 'Killing any stale ii sessions'
killall ii

function _quit() {
        echo '/quit' > "$II_PATH/$TARGET/in"
        exit
}

trap _quit INT

while true; do
        echo "Connecting to $TARGET:$PORT"
        ii -i "$II_PATH" -s "$TARGET" -p "$PORT" -n "$NICK" -f "$REALNAME" &
        iipid="$!"

        sleep 3
        echo "Joining $CHANNEL"
        echo "/j $CHANNEL" > "$II_PATH/$TARGET/in"
        wait "$iipid"
done
