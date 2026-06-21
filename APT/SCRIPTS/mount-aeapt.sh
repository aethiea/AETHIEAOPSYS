#!/usr/bin/env bash
# BEGIN AETHIEA_MARKER_RESOLVE
_aeth_resolve_root() {
  local p="${AETHIEA_ROOT:-${AETH_ROOT:-${AETHIEA:-${AETHIEAOPSYS:-$(pwd -P)}}}}"
  if [ -n "$p" ] && [ -f "$p/.aeth_root" ]; then (cd "$p" && pwd -P); return; fi
  p="$(pwd -P)"
  while [ "$p" != "/" ] && [ ! -f "$p/.aeth_root" ]; do p="$(dirname "$p")"; done
  if [ -f "$p/.aeth_root" ]; then (cd "$p" && pwd -P); return; fi
  for p in /mnt/*/AETHIEAOPSYS "$HOME/AETHIEAOPSYS" /opt/AETHIEAOPSYS; do
    [ -f "$p/.aeth_root" ] && { (cd "$p" && pwd -P); return; }
  done
  return 1
}
AETHIEA_ROOT="$(_aeth_resolve_root)" || { echo "NO_AETH_ROOT_FOUND"; exit 1; }
export AETHIEA_ROOT AETH_ROOT="$AETHIEA_ROOT" AETHIEA="$AETHIEA_ROOT" AETHIEAOPSYS="$AETHIEA_ROOT"
# END AETHIEA_MARKER_RESOLVE

set -euo pipefail

AETHIEA="${AETHIEA:-$AETHIEA_ROOT}"
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
