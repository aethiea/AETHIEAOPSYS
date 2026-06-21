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
LOG_DIR="$AETHIEA_ROOT/LOGS/HERMES"
mkdir -p "$LOG_DIR"

echo "HERMES ONLINE"
echo "Root: $AETHIEA_ROOT"
echo "Mode: AEUSB_CARRIED"
echo "Role: courier / interface membrane"
echo "Doctrine: Host executes. AEUSB carries. Host does not own."
echo "Timestamp UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG_DIR/hermes_boot.log"
