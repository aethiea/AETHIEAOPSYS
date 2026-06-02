#!/usr/bin/env bash
set -euo pipefail

AETHIEA="${AETHIEA:-/mnt/h/AETHIEAOPSYS}"
MNT="$AETHIEA/APT/MOUNTS/rootfs"

for p in run sys proc dev/pts dev; do
  if mountpoint -q "$MNT/$p"; then
    sudo umount "$MNT/$p"
  fi
done

if mountpoint -q "$MNT"; then
  sudo umount "$MNT"
fi

echo "AEAPT unmounted → $MNT"
