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

AETHIEA_ROOT="${AETHIEA_ROOT:-$AETHIEA_ROOT}"
MANIFEST_DIR="$AETHIEA_ROOT/APT/manifests"
LOG_DIR="$AETHIEA_ROOT/LOGS/SYSTEM"

mkdir -p "$LOG_DIR"

echo "AETHIEA RUBIII REBUILD BASELINE"
echo "Root: $AETHIEA_ROOT"
echo "Doctrine: #butnotlimitedTEWW"
echo "This rebuild script restores a known baseline, not an exhaustive boundary."

sudo apt update

if ls "$MANIFEST_DIR"/rubiii_manual_packages_after_upgrade_*.txt >/dev/null 2>&1; then
  MANUAL_FILE="$(ls -t "$MANIFEST_DIR"/rubiii_manual_packages_after_upgrade_*.txt | head -n 1)"
elif ls "$MANIFEST_DIR"/rubiii_manual_packages_postupdate_*.txt >/dev/null 2>&1; then
  MANUAL_FILE="$(ls -t "$MANIFEST_DIR"/rubiii_manual_packages_postupdate_*.txt | head -n 1)"
else
  MANUAL_FILE="$(ls -t "$MANIFEST_DIR"/rubiii_manual_packages_*.txt | head -n 1)"
fi

echo "Using manual package baseline: $MANUAL_FILE"

xargs -r sudo apt install -y < "$MANUAL_FILE"

echo "Rebuild baseline complete."
echo "Confirmed here, not confined here."
