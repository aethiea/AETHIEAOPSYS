#!/usr/bin/env bash
set -euo pipefail

ROOT="${AETHIEA:-${AETH_ROOT:-}}"

if [ -z "$ROOT" ] || [ ! -d "$ROOT" ]; then
  for candidate in /opt/AETHIEAOPSYS /mnt/h/AETHIEAOPSYS /mnt/e/AETHIEAOPSYS /mnt/d/AETHIEAOPSYS "$HOME/AETHIEAOPSYS"; do
    if [ -f "$candidate/.aeth_root" ] || [ -d "$candidate/CORE" ]; then
      ROOT="$candidate"
      break
    fi
  done
fi

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
    "This surface confirms a pattern but does not limit the system",
    "System-wide non-closure clause applies unless explicitly sealed"
  ]
}
JSON

python3 -m json.tool "$SURFACE_FILE" >/dev/null
echo "SURFACE REGISTERED → $SURFACE_FILE"
