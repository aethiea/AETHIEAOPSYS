#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import socket
import tempfile
from datetime import datetime, timezone
from pathlib import Path


EXPECTED = (
    "LAYERS/AEG/config.json",
    "LAYERS/AEG/resolve.py",
    "LAYERS/AEB/config.json",
    "LAYERS/AEB/derive.py",
    "LAYERS/AEHUB/config.json",
    "LAYERS/AEHUB/status.py",
    "SURFACES/AEVPS/config.json",
    "CONFIG/AECLOUD/aevps-001.route.json",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    components = {
        relative: (root / relative).is_file()
        for relative in EXPECTED
    }
    missing = [relative for relative, present in components.items() if not present]

    payload = {
        "schema": "aethiea.aehub.component-status.v1",
        "utc": utc_now(),
        "host": socket.gethostname(),
        "release_root": str(root),
        "release_commit": os.environ.get("AETHIEA_RELEASE_COMMIT", "unknown"),
        "authority": False,
        "public_exposure": False,
        "cloudflare_mutation": False,
        "components": components,
        "missing": missing,
        "state": "PASS" if not missing else "FAIL",
    }

    if args.output:
        write_atomic(Path(args.output), payload)

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not missing else 3


if __name__ == "__main__":
    raise SystemExit(main())
