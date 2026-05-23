#!/usr/bin/env bash
# Mount one or more Windows drives under /mnt/<letter> with current user ownership.
# Usage: sudo ./mount-windows-drives.sh D E ...

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
    echo "Run with sudo." >&2
    exit 1
fi

if [ "$#" -eq 0 ]; then
    echo "Usage: sudo $0 <drive-letter> [<drive-letter> ...]" >&2
    echo "Example: sudo $0 D E" >&2
    exit 1
fi

# Use the invoking user's uid/gid (SUDO_UID/SUDO_GID are set by sudo)
UID_OPT="${SUDO_UID:-$(id -u)}"
GID_OPT="${SUDO_GID:-$(id -g)}"

for letter in "$@"; do
    letter="${letter%%:}"          # strip trailing colon if present
    upper="${letter^^}"
    mountpoint="/mnt/${letter,,}"  # lowercase for the path

    mkdir -p "$mountpoint"

    if mountpoint -q "$mountpoint"; then
        mount -o "remount,uid=${UID_OPT},gid=${GID_OPT}" "$mountpoint"
    else
        mount -t drvfs "${upper}:" "$mountpoint" -o "uid=${UID_OPT},gid=${GID_OPT}"
    fi
    echo "Mounted ${upper}: → ${mountpoint} (uid=${UID_OPT}, gid=${GID_OPT})"
done
