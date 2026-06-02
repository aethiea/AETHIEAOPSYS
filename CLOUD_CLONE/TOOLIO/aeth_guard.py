#!/usr/bin/env python3
import json
import os
import shlex
import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("AETHIEA", Path.cwd())).resolve()
TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")

REPORT_DIR = ROOT / "EXECUTION" / "REPORTS" / "GUARD"

SNAPSHOT_DIR = ROOT / "DATA" / "MEMORY" / "SNAPSHOTS" / "GUARD"

SNAPSHOT_TARGETS = [
    ROOT / "CORE",
    ROOT / "DATA" / "MEMORY" / "SYSTEM",
    ROOT / "DATA" / "MEMORY" / "STATE",
    ROOT / "LAYERS",
    ROOT / "EXECUTION" / "REPORTS"
]

SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

def snapshot_state(ts: str):
    snap = {}

    for target in SNAPSHOT_TARGETS:
        if not target.exists():
            continue

        if target.is_dir():
            files = sorted([
                str(p.relative_to(ROOT))
                for p in target.rglob("*")
                if p.is_file()
            ])[:2000]

            snap[str(target.relative_to(ROOT))] = {
                "type": "directory",
                "file_count": len(files),
                "files": files[:200]
            }

        elif target.is_file():
            snap[str(target.relative_to(ROOT))] = {
                "type": "file",
                "sha256": sha256_file(target)
            }

    out = SNAPSHOT_DIR / f"{ts}_snapshot.json"
    write_json(out, snap)
    return out


LOG_DIR = ROOT / "LOGS" / "GUARD"
ANCHOR_DIR = ROOT / "DATA" / "MEMORY" / "ANCHORS"
REJECTED_DIR = ROOT / "REJECTED" / "GUARD"

for d in (REPORT_DIR, LOG_DIR, ANCHOR_DIR, REJECTED_DIR):
    d.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def main():
    if len(sys.argv) < 2:
        print('USAGE: aeth guard "<command>"')
        raise SystemExit(2)

    command = " ".join(sys.argv[1:]).strip()
    started = datetime.now(timezone.utc)

    snapshot = snapshot_state(TS)


    proc = subprocess.run(
        command,
        shell=True,
        cwd=str(ROOT),
        text=True,
        capture_output=True
    )

    ended = datetime.now(timezone.utc)
    status = "PASS" if proc.returncode == 0 else "FAIL"

    payload = {
        "schema": "AETHIEA.guard.report.v1",
        "snapshot": str(snapshot.relative_to(ROOT)),
        "timestamp_utc": TS,
        "root": str(ROOT),
        "command": command,
        "returncode": proc.returncode,
        "status": status,
        "started_utc": started.isoformat(),
        "ended_utc": ended.isoformat(),
        "stdout": proc.stdout[-8000:],
        "stderr": proc.stderr[-8000:],
        "runtime_duties": [
            "execute",
            "capture_stdout",
            "capture_stderr",
            "check_return_code",
            "write_report",
            "write_anchor",
            "sync_cloud"
        ]
    }

    safe = "".join(c if c.isalnum() else "_" for c in command[:60]).strip("_")
    report = REPORT_DIR / f"{TS}_{safe}.json"
    log = LOG_DIR / f"{TS}_{safe}.log"
    anchor = ANCHOR_DIR / f"{TS}_guard_{status.lower()}.json"

    write_json(report, payload)

    log.write_text(
        f"COMMAND: {command}\nSTATUS: {status}\nRETURN: {proc.returncode}\n\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}\n",
        encoding="utf-8"
    )

    write_json(anchor, {
        "anchor": f"AETHIEA guard {status}: {command}",
        "timestamp_utc": TS,
        "report": str(report.relative_to(ROOT)),
        "log": str(log.relative_to(ROOT)),
        "returncode": proc.returncode,
        "status": status
    })

    hashes = {
        "report_sha256": sha256_file(report),
        "log_sha256": sha256_file(log),
        "anchor_sha256": sha256_file(anchor)
    }

    payload["hashes"] = hashes
    write_json(report, payload)

    anchor_payload = json.loads(anchor.read_text(encoding="utf-8"))
    anchor_payload["hashes"] = hashes
    write_json(anchor, anchor_payload)

    sync_status = "SKIPPED"
    sync_returncode = None
    sync_script = ROOT / "TOOLIO" / "aeth_cloud_clone.py"

    if sync_script.exists():
        sync = subprocess.run(
            ["python3", str(sync_script)],
            cwd=str(ROOT),
            text=True,
            capture_output=True
        )
        sync_status = "PASS" if sync.returncode == 0 else "FAIL"
        sync_returncode = sync.returncode


    rejected_file = None
    if status == "FAIL":
        rejected_file = REJECTED_DIR / f"{TS}_{safe}_rejected.json"
        write_json(rejected_file, {
            "schema": "AETHIEA.guard.rejected.v1",
            "timestamp_utc": TS,
            "command": command,
            "returncode": proc.returncode,
            "stderr": proc.stderr[-4000:],
            "stdout": proc.stdout[-4000:],
            "report": str(report.relative_to(ROOT)),
            "log": str(log.relative_to(ROOT)),
            "status": "REJECTED"
        })
        payload["rejected"] = str(rejected_file.relative_to(ROOT))

    payload["cloud_sync"] = {
        "status": sync_status,
        "returncode": sync_returncode
    }
    write_json(report, payload)

    print(f"GUARD_{status} → {command}")
    print(f"REPORT → {report}")
    print(f"ANCHOR → {anchor}")
    print(f"CLOUD_SYNC → {sync_status}")

    raise SystemExit(proc.returncode)

if __name__ == "__main__":
    main()
