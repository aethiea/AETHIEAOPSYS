#!/usr/bin/env python3
from pathlib import Path
import json
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: python3 TOOLIO/aeth_diff.py <map_a.json> <map_b.json>")

a = json.loads(Path(sys.argv[1]).read_text())
b = json.loads(Path(sys.argv[2]).read_text())

A = {r["rel"]: r for r in a["records"]}
B = {r["rel"]: r for r in b["records"]}

missing_in_b = sorted(set(A) - set(B))
missing_in_a = sorted(set(B) - set(A))
changed = sorted(
    k for k in set(A) & set(B)
    if A[k].get("sha256") and B[k].get("sha256") and A[k].get("sha256") != B[k].get("sha256")
)

print("=== AETHIEA DIFF ===")
print("MAP_A:", sys.argv[1])
print("MAP_B:", sys.argv[2])
print()
print("MISSING_IN_B:", len(missing_in_b))
for x in missing_in_b[:100]:
    print(" -", x)

print()
print("MISSING_IN_A:", len(missing_in_a))
for x in missing_in_a[:100]:
    print(" +", x)

print()
print("CHANGED:", len(changed))
for x in changed[:100]:
    print(" *", x)
