#!/usr/bin/env bash
set -euo pipefail

AETHIEA="${AETHIEA:-/mnt/h/AETHIEAOPSYS}"
IMG="$AETHIEA/APT/IMAGES/aethiea-apt-rootfs.ext4"
MNT="$AETHIEA/APT/MOUNTS/rootfs"

mkdir -p "$MNT"

if mountpoint -q "$MNT"; then
  echo "AEAPT already mounted → $MNT"
  exit 0
fi

sudo mount -o loop "$IMG" "$MNT"

sudo mount --bind /dev "$MNT/dev"
sudo mount --bind /dev/pts "$MNT/dev/pts"
sudo mount --bind /proc "$MNT/proc"
sudo mount --bind /sys "$MNT/sys"
sudo mount --bind /run "$MNT/run"

echo "AEAPT mounted → $MNT"
