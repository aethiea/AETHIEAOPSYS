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

ROOT="$(aeth_resolve_body)" || {
  echo "STOP: AETHIEAOPSYS body not found by markers"
  exit 1
}

export AETHIEA="$ROOT"
export AETH_ROOT="$ROOT"
export AETHIEA_ROOT="$ROOT"

echo "=== OPERATOR RESOLUTION ==="
echo

python3 - <<'INNERPY'
import json
import os
from pathlib import Path

root = Path(os.environ["AETHIEA"])
f = root / "DATA/MEMORY/OPERATOR/operator_invariants.json"

data = json.loads(f.read_text())

print(f"operator  -> {data['operator']}")
print(f"node      -> {data['node']}")
print(f"profile   -> {data['profile']}")
print(f"interface -> {data['interface']}")
print()

print("LAWS")
for x in data["laws"]:
    print(f"- {x}")

print()
print("ROUTING")
for k, v in data["routing"].items():
    print(f"{k} -> {v}")
INNERPY
