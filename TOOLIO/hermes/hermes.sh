#!/usr/bin/env bash
set -euo pipefail

aeth_valid_body() {
  [ -n "${1:-}" ] || return 1
  [ -d "$1" ] || return 1
  [ -f "$1/.aeth_root" ] || return 1
  [ -f "$1/STATUS.md" ] || return 1
  [ ! -f "$1/AE320GB_HEAVY_BODY" ] || return 1
  [ ! -f "$1/.aeth_heavy_body" ] || return 1
}

aeth_resolve_body() {
  local c d r

  for c in "${AETHIEA:-}" "${AETH_ROOT:-}" "${AETHIEA_ROOT:-}" "$PWD"; do
    [ -n "$c" ] || continue
    d="$c"
    while [ "$d" != "/" ]; do
      if aeth_valid_body "$d"; then
        printf '%s\n' "$d"
        return 0
      fi
      d="$(dirname "$d")"
    done
  done

  for r in /mnt/[a-z]/AETHIEAOPSYS; do
    if aeth_valid_body "$r"; then
      printf '%s\n' "$r"
      return 0
    fi
  done

  return 1
}

AETHIEA_ROOT="$(aeth_resolve_body)" || {
  echo "STOP: AETHIEAOPSYS body not found by markers"
  exit 1
}

export AETHIEA="$AETHIEA_ROOT"
export AETH_ROOT="$AETHIEA_ROOT"
export AETHIEA_ROOT

LOG_DIR="$AETHIEA_ROOT/LOGS/HERMES"
mkdir -p "$LOG_DIR"

echo "HERMES ONLINE"
echo "Root: $AETHIEA_ROOT"
echo "Mode: AEUSB_CARRIED"
echo "Role: courier / interface membrane"
echo "Doctrine: Host executes. AEUSB carries. Host does not own."
echo "Timestamp UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG_DIR/hermes_boot.log"
