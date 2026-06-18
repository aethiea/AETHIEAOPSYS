#!/usr/bin/env bash
set -euo pipefail

valid_root() {
  local r="$1"
  [ -n "$r" ] || return 1
  [ -d "$r" ] || return 1
  [ -f "$r/.aeth_root" ] || return 1
  [ -f "$r/STATUS.md" ] || return 1
  [ ! -f "$r/AE320GB_HEAVY_BODY" ] || return 1
  [ ! -f "$r/.aeth_heavy_body" ] || return 1
}

resolve_root() {
  local r d

  if declare -F aeth_root >/dev/null 2>&1; then
    r="$(aeth_root 2>/dev/null || true)"
    valid_root "$r" && { printf '%s\n' "$r"; return 0; }
  fi

  for r in "${AETHIEA:-}" "${AETH_ROOT:-}" "${AETHIEAOPSYS:-}" "${AEUSB:-}"; do
    valid_root "$r" && { printf '%s\n' "$r"; return 0; }
  done

  d="$PWD"
  while [ "$d" != "/" ]; do
    valid_root "$d" && { printf '%s\n' "$d"; return 0; }
    d="$(dirname "$d")"
  done

  for r in /mnt/[a-z]/AETHIEAOPSYS /media/*/AETHIEAOPSYS /run/media/*/AETHIEAOPSYS /Volumes/*/AETHIEAOPSYS "$HOME/AETHIEAOPSYS" /opt/AETHIEAOPSYS; do
    valid_root "$r" && { printf '%s\n' "$r"; return 0; }
  done

  return 1
}

ROOT="$(resolve_root || true)"

if [ -z "$ROOT" ] || [ ! -d "$ROOT" ]; then
  echo "SURFACE REGISTER ERROR → AETHIEA root not found" >&2
  exit 1
fi

HOST_ID="$(hostname | tr '[:lower:]' '[:upper:]')"
HOST_FILE="$(hostname | tr '[:upper:]' '[:lower:]')"
SURFACE_DIR="$ROOT/DATA/MEMORY/SURFACES"
SURFACE_FILE="$SURFACE_DIR/${HOST_FILE}.json"

mkdir -p "$SURFACE_DIR"

cat > "$SURFACE_FILE" <<JSON
{
  "id": "$HOST_ID",
  "type": "canonical_interface_surface",
  "classification": "surface_layer",
  "relationship": "renders_and_interacts_with_AETHIEAOPSYS",
  "host_role": "execution_and_interface",
  "runtime": "AETHIEAOPSYS",
  "runtime_root": "$ROOT",
  "mode": "${AETHIEA_MODE:-USB_CONTINUITY}",
  "operator_node": "DNY-5U5",
  "status": "ACTIVE",
  "rules": [
    "$HOST_ID is not AETHIEA",
    "$HOST_ID is not AETHIEAOPSYS",
    "$HOST_ID is a canonical surface/interface layer",
    "Hosts provide execution only",
    "Continuity belongs to AETHIEAOPSYS",
    "USB carries the continuity body",
    "Host state is temporary unless explicitly registered",
    "#butnotlimitedTEWW",
    "Visible example does not close topology",
    "System-wide non-closure clause applies unless explicitly sealed"
  ]
}
JSON

python3 -m json.tool "$SURFACE_FILE" >/dev/null
echo "SURFACE REGISTERED → $SURFACE_FILE"
