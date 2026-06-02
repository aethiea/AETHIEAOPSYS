#!/usr/bin/env bash
set -euo pipefail

ROOT="${AETHIEA:-/mnt/e/AETHIEAOPSYS}"

echo "=== OPERATOR RESOLUTION ==="
echo

python3 - <<PY
import json
from pathlib import Path

root = Path("$ROOT")
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
for k,v in data["routing"].items():
    print(f"{k} -> {v}")
PY
