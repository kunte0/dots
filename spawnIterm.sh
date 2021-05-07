#!/usr/bin/env bash

set -e

osascript - <<EOF
tell application "iTerm2"
    create window with default profile
end tell
EOF
