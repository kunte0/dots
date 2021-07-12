#!/usr/bin/env bash

set -e


if ! pgrep -f "iTerm" > /dev/null 2>&1; then
    open -a "/Applications/iTerm.app"
else
    osascript - <<EOF
tell application "iTerm2"
    create window with default profile
end tell
EOF
fi
