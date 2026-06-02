#!/usr/bin/env python3
import subprocess, json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path.cwd()
TS = datetime.now(timezone.utc).isoformat()

def sh(cmd):
    r = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    return {"cmd": cmd, "code": r.returncode, "stdout": r.stdout.strip(), "stderr": r.stderr.strip()}

checks = {
    "services": sh("systemctl status aeth-portal cloudflared aeth-cloud-sync --no-pager"),
    "local": sh("curl -I -s http://localhost:3000 | head -n 1"),
    "external": sh("curl -I -s https://aether.thematriculation.cc | head -n 1"),
    "anchors": sh("ls -lt DATA/MEMORY/ANCHORS | head")
}

out = ROOT / "DATA/MEMORY/STATE/latest_verify_stack.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"timestamp_utc": TS, "checks": checks}, indent=2) + "\n")
print("VERIFY_STACK_WRITTEN →", out)
print(checks["local"]["stdout"])
print(checks["external"]["stdout"])
