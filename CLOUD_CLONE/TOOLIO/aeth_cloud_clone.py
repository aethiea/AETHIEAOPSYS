#!/usr/bin/env python3
import json
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(os.environ.get("AETHIEA", Path.cwd())).resolve()
CLOUD = Path(os.environ.get("AETHIEA_CLOUD_CLONE", str(ROOT / "CLOUD_CLONE"))).resolve()

TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")

ROUTES = {
    "DATA/MEMORY/SYSTEM": "DATA/MEMORY/SYSTEM",
    "DATA/MEMORY/STATE": "DATA/MEMORY/STATE",
    "DATA/MEMORY/SESSIONS": "DATA/MEMORY/SESSIONS",
    "DATA/MEMORY/ROUTES": "DATA/MEMORY/ROUTES",
    "DATA/MEMORY/NODES": "DATA/MEMORY/NODES",
    "DATA/MEMORY/ANCHORS": "DATA/MEMORY/ANCHORS",
    "DATA/MEMORY/HOSTS": "DATA/MEMORY/HOSTS",
    "DATA/MEMORY/METRICS": "DATA/MEMORY/METRICS",
    "DATA/MEMORY/SNAPSHOTS": "DATA/MEMORY/SNAPSHOTS",
    "MODS/B43-RU5": "MODS/B43-RU5",
    "MODS/P47H30N": "MODS/P47H30N",
    "LAYERS": "LAYERS",
    "EXECUTION/REPORTS": "EXECUTION/REPORTS",
    "EXECUTION/PIPELINES": "EXECUTION/PIPELINES",
    "DOMAINS": "DOMAINS",
    "GCR": "GCR",
    "LOGS": "LOGS",
    "TOOLIO": "TOOLIO"
}

EXCLUDE_DIRS = {
    "__pycache__",
    ".git",
    "ENV",
    "TEMP",
    "RUN",
    "CLOUD_CLONE"
}

def keep(path: Path) -> bool:
    return not any(part in EXCLUDE_DIRS for part in path.parts)

def copy_file(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime and dst.stat().st_size == src.stat().st_size:
        return False
    shutil.copyfile(src, dst)
    return True

def sync_dir(src_dir: Path, dst_dir: Path):
    copied = []
    if not src_dir.exists():
        return copied

    for src in src_dir.rglob("*"):
        if not src.is_file() or not keep(src):
            continue

        rel = src.relative_to(src_dir)
        dst = dst_dir / rel

        if copy_file(src, dst):
            copied.append(str(src.relative_to(ROOT)))

    return copied

def write_receipt(copied):
    receipt_dir = ROOT / "DATA" / "MEMORY" / "ANCHORS"
    receipt_dir.mkdir(parents=True, exist_ok=True)

    receipt = {
        "anchor": "AETHIEA cloud clone sync",
        "timestamp_utc": TS,
        "root": str(ROOT),
        "cloud_clone": str(CLOUD),
        "mode": "passive_append_preserve",
        "delete_remote": False,
        "routes": ROUTES,
        "files_copied": copied,
        "count": len(copied),
        "status": "LOCKED"
    }

    local_receipt = receipt_dir / f"{TS}_cloud_clone_sync.json"
    local_receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    cloud_receipt = CLOUD / "DATA" / "MEMORY" / "ANCHORS" / local_receipt.name
    copy_file(local_receipt, cloud_receipt)

    return local_receipt, cloud_receipt

def main():
    CLOUD.mkdir(parents=True, exist_ok=True)

    copied = []
    for local, remote in ROUTES.items():
        src = ROOT / local
        dst = CLOUD / remote
        copied.extend(sync_dir(src, dst))

    local_receipt, cloud_receipt = write_receipt(copied)

    print("AETHIEA CLOUD CLONE SYNC COMPLETE")
    print(f"ROOT        → {ROOT}")
    print(f"CLOUD CLONE → {CLOUD}")
    print(f"FILES       → {len(copied)}")
    print(f"LOCAL LOG   → {local_receipt}")
    print(f"CLOUD LOG   → {cloud_receipt}")

if __name__ == "__main__":
    main()
