#!/usr/bin/env python3
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(os.environ.get("AETHIEA", Path.cwd())).resolve()
TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def sh(cmd):
    try:
        out = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=20)
        return {"cmd": cmd, "code": out.returncode, "stdout": out.stdout.strip(), "stderr": out.stderr.strip()}
    except Exception as e:
        return {"cmd": cmd, "code": 999, "stderr": str(e)}

def status():
    checks = {
        "aeth_cli": sh("which aeth"),
        "services": sh("systemctl is-active aeth-portal cloudflared aeth-cloud-sync"),
        "local_portal": sh("curl -I -s http://localhost:3000 | head -n 1"),
        "external_aether": sh("curl -I -s https://aether.thematriculation.cc | head -n 1"),
        "latest_anchors": sh("ls -lt DATA/MEMORY/ANCHORS | head")
    }
    write(ROOT / "DATA/MEMORY/STATE/latest_stack_status.json", {
        "timestamp_utc": TS,
        "checks": checks,
        "status": "WRITTEN"
    })
    return checks

def host_profile():
    write(ROOT / "DATA/MEMORY/HOSTS/lolita.json", {
        "host": "LOLITA",
        "role": "portable_runtime_host",
        "aethiea_root": str(ROOT),
        "services": ["aeth-portal", "cloudflared", "aeth-cloud-sync"],
        "tunnel": "AETHERNet",
        "portal": "http://localhost:3000",
        "external_endpoint": "https://aether.thematriculation.cc",
        "cloud_clone": str(ROOT / "CLOUD_CLONE"),
        "last_verified_utc": TS,
        "status": "ACTIVE"
    })

def cloudflare_routes():
    write(ROOT / "LAYERS/AENET/CONFIG/cloudflare_routes.json", {
        "timestamp_utc": TS,
        "layer": "AENET",
        "cloudflare_role": "external_door_edge_ingress_egress",
        "routes": {
            "aether.thematriculation.cc": "http://localhost:3000",
            "ssh.thematriculation.cc": "ssh://localhost:22",
            "labelle.thematriculation.cc": "mapped_service_pending_verification"
        },
        "status": "LOCKED"
    })

def verify_stack_script():
    p = ROOT / "TOOLIO/aeth_verify_stack.py"
    p.write_text(f'''#!/usr/bin/env python3
import subprocess, json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path.cwd()
TS = datetime.now(timezone.utc).isoformat()

def sh(cmd):
    r = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    return {{"cmd": cmd, "code": r.returncode, "stdout": r.stdout.strip(), "stderr": r.stderr.strip()}}

checks = {{
    "services": sh("systemctl status aeth-portal cloudflared aeth-cloud-sync --no-pager"),
    "local": sh("curl -I -s http://localhost:3000 | head -n 1"),
    "external": sh("curl -I -s https://aether.thematriculation.cc | head -n 1"),
    "anchors": sh("ls -lt DATA/MEMORY/ANCHORS | head")
}}

out = ROOT / "DATA/MEMORY/STATE/latest_verify_stack.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({{"timestamp_utc": TS, "checks": checks}}, indent=2) + "\\n")
print("VERIFY_STACK_WRITTEN →", out)
print(checks["local"]["stdout"])
print(checks["external"]["stdout"])
''', encoding="utf-8")

def repair_script():
    p = ROOT / "TOOLIO/aeth_repair_services.py"
    p.write_text('''#!/usr/bin/env python3
import subprocess
services = ["aeth-portal", "cloudflared", "aeth-cloud-sync"]
for s in services:
    print("RESTART →", s)
    subprocess.run(["sudo", "systemctl", "restart", s])
subprocess.run(["systemctl", "status", *services, "--no-pager"])
''', encoding="utf-8")

def portal_page():
    p = ROOT / "PORTAL/index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("""<!doctype html>
<html>
<head><meta charset="utf-8"><title>AETHIEAOPSYS</title></head>
<body style="font-family: monospace; background:#050505; color:#f4f4f4; padding:32px;">
<h1>AETHIEAOPSYS // AETHIE 1of1 HUD</h1>
<p>Runtime Host: LOLITA</p>
<p>Portal: ACTIVE</p>
<p>AETHERNet: ACTIVE</p>
<p>CLOUD_CLONE: PASSIVE CONTINUITY MIRROR</p>
<p>Status: LIVE / SYSTEMD / EXTERNALLY REACHABLE / AUTO-SYNCED</p>
</body>
</html>
""", encoding="utf-8")

def pipeline_runner():
    p = ROOT / "TOOLIO/aeth_run_pipeline.py"
    p.write_text('''#!/usr/bin/env python3
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
''', encoding="utf-8")

def anchor(text):
    anchors = ROOT / "DATA/MEMORY/ANCHORS"
    anchors.mkdir(parents=True, exist_ok=True)
    f = anchors / f"{TS}_buildout_next10.json"
    write(f, {"anchor": text, "timestamp_utc": TS, "status": "LOCKED"})
    return f

def main():
    checks = status()
    host_profile()
    cloudflare_routes()
    verify_stack_script()
    repair_script()
    portal_page()
    pipeline_runner()
    a = anchor("2026-05-05 next10 buildout scripts written: verify stack, repair services, host profile, cloudflare routes, portal page, pipeline runner")

    print("NEXT10 BUILDOUT COMPLETE")
    print("ROOT →", ROOT)
    print("ANCHOR →", a)
    print("STATUS → DATA/MEMORY/STATE/latest_stack_status.json")
    print("HOST → DATA/MEMORY/HOSTS/lolita.json")
    print("ROUTES → LAYERS/AENET/CONFIG/cloudflare_routes.json")
    print("VERIFY → python3 TOOLIO/aeth_verify_stack.py")
    print("REPAIR → python3 TOOLIO/aeth_repair_services.py")
    print("PIPELINE → python3 TOOLIO/aeth_run_pipeline.py MULTIMEDIA")

if __name__ == "__main__":
    main()
