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
