#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT = Path.cwd()

if len(sys.argv) < 2:
    print("USAGE: aeth_run_pipeline.py PIPELINE")
    raise SystemExit(1)

pipe = sys.argv[1].upper()
binding = ROOT / "EXECUTION" / "PIPELINES" / pipe / "binding.json"

if not binding.exists():
    print(f"PIPELINE_BINDING_MISSING → {binding}")
    raise SystemExit(1)

data = json.loads(binding.read_text())
seq = data.get("bae_sequence", [])
rules = data.get("rules", {})

print(f"LOAD PIPELINE: {pipe}")
print("BÆ SEQUENCE:", ",".join(seq))
print("CHECK: compliance required =", rules.get("must_pass_compliance"))
print("CHECK: containment required =", rules.get("must_check_containment"))
print("CHECK: human approval required =", rules.get("human_approval_required"))
print("STATUS: READY_FOR_OPERATOR")
