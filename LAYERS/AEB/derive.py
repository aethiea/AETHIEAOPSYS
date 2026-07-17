#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path


STAGES = (
    "conceptual",
    "decontextualized",
    "generalized",
    "normalized",
    "operationalized",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(path: Path, payload: dict[str, object]) -> None:
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
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--stage", choices=STAGES, default="conceptual")
    parser.add_argument("--routing-class", required=True)
    parser.add_argument("--sensitivity-class", default="internal")
    parser.add_argument(
        "--source-authority",
        choices=("canonical", "historical", "external", "operator-provided"),
        required=True,
    )
    parser.add_argument("--source-type", default="record")
    parser.add_argument("--invariant", action="append", default=[])
    parser.add_argument("--constraint", action="append", default=[])
    parser.add_argument("--derived-claim", action="append", default=[])
    parser.add_argument("--parent-abstraction-id")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    output = Path(args.output).resolve()

    if not source.is_file():
        print(f"SOURCE_NOT_FOUND={source}", file=sys.stderr)
        return 2

    source_hash = sha256_file(source)
    record = {
        "schema": "aethiea.aeb.abstraction-record.v1",
        "source_id": f"sha256:{source_hash}",
        "source_hash": source_hash,
        "source_path": str(source),
        "source_type": args.source_type,
        "source_authority": args.source_authority,
        "abstraction_id": str(uuid.uuid4()),
        "abstraction_stage": args.stage,
        "invariants": args.invariant,
        "discarded_context": [],
        "preserved_constraints": args.constraint,
        "derived_claims": args.derived_claim,
        "provenance": [
            {
                "event": "aeb_record_created",
                "utc": utc_now(),
                "tool": "LAYERS/AEB/derive.py",
            }
        ],
        "routing_class": args.routing_class,
        "sensitivity_class": args.sensitivity_class,
        "validation_state": "draft",
        "promotion_state": "unpromoted",
        "execution_authority": "none",
        "created_utc": utc_now(),
        "parent_abstraction_id": args.parent_abstraction_id,
        "source_preserved": True,
        "generated_is_canonical": False,
    }

    atomic_write_json(output, record)
    print(f"AEB_RECORD={output}")
    print(f"SOURCE_SHA256={source_hash}")
    print("PROMOTION_STATE=unpromoted")
    print("SOURCE_PRESERVED=TRUE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
