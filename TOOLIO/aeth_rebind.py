#!/usr/bin/env python3
from pathlib import Path
import json
from datetime import datetime, UTC

START = Path.cwd().resolve()

def find_root(p):
    markers = ["CORE","DATA","DOMAINS","EXECUTION","LAYERS","LOGS","MODS","TOOLIO"]
    for cur in [p] + list(p.parents):
        if all((cur / m).exists() for m in markers):
            return cur
    raise SystemExit("AETHIEAOPSYS root not found")

ROOT = find_root(START)
ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

state = ROOT / "DATA/MEMORY/STATE/current_host.json"
state.parent.mkdir(parents=True, exist_ok=True)

data = {
    "schema": "AETHIEA_REBIND",
    "root": str(ROOT),
    "host_path": str(ROOT),
    "rule": "relative paths are authoritative; absolute paths are host bindings",
    "timestamp_utc": ts
}

state.write_text(json.dumps(data, indent=2), encoding="utf-8")

print("AETHIEA_ROOT:", ROOT)
print("STATE:", state)
