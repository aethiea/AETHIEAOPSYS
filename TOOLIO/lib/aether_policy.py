#!/usr/bin/env python3

import json
import os
import re
import sys
from pathlib import Path


HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from aether_hostless import resolve_heavy, resolve_root


ROOT = resolve_root()

FORBIDDEN_PATTERNS = [
    (
        re.compile(r"\bmount\s+-t\s+drvfs\s+[A-Z]:", re.I),
        "FORCED_DRIVE_HOST_BIND",
    ),
    (
        re.compile(r"\bsudo\s+mount\b", re.I),
        "SUDO_MOUNT_HOST_BIND_MECHANIC",
    ),
    (
        re.compile(
            r"export\s+AETHIEA_ROOT=.*/mnt/[a-z]/AETHIEAOPSYS",
            re.I,
        ),
        "STATIC_AUTHORITY_ENV_EXPORT",
    ),
    (
        re.compile(r"AETHIEA_FORCE_MOUNT_AEUSB\s*=\s*1", re.I),
        "FORCE_MOUNT_FLAG_ENABLED",
    ),
    (
        re.compile(r"AETHIEA_HOST_BIND\s*=\s*1", re.I),
        "HOST_BIND_FLAG_ENABLED",
    ),
    (
        re.compile(r'ROOT="/home/[^"]*/AETHIEAOPSYS"', re.I),
        "HARDCODED_HOME_ROOT",
    ),
    (
        re.compile(r"/mnt/h/AETHIEAOPSYS", re.I),
        "STALE_H_AUTHORITY_REFERENCE",
    ),
    (
        re.compile(r"/mnt/i/AETHIEAOPSYS", re.I),
        "STALE_I_HEAVY_REFERENCE",
    ),
    (
        re.compile(r"/mnt/j/AETHIEAOPSYS", re.I),
        "STATIC_AEUSB_HOST_PATH",
    ),
    (
        re.compile(r"/mnt/k/AETHIEAOPSYS", re.I),
        "STATIC_AEXHD_HOST_PATH",
    ),
]

EXCLUDE_PARTS = {
    "archive",
    "backups",
    "cache",
    "quarantine",
    "receipts",
    "storage",
    "__pycache__",
}

EXCLUDE_FILES = {
    "aether_policy.py",
    "aether_hostless.py",
    "aether-guard",
    "aether-preflight",
    "aether-hostless-repair",
    "aether-hostless-clean-active",
    "aether-hostless-final-proof",
}


def load_policy():
    path = ROOT / "CONFIG/authority/aether-system-policy.json"
    return json.loads(path.read_text())


def validate_policy(policy):
    body = policy.get("policy", {})
    errors = []

    if policy.get("lock") != "BOUND_LESS_ONLY_BIND_TO_AETHER":
        errors.append("LOCK_NOT_BOUNDLESS_AETHER")

    checks = {
        "bind_to": "AETHER",
        "host_bind_allowed": False,
        "force_mount_aeusb_allowed": False,
        "drive_letter_authority_allowed": False,
        "tool_second_body_allowed": False,
        "aethieaopsys_is_source_body": True,
    }

    for key, expected in checks.items():
        if body.get(key) != expected:
            errors.append(f"{key}_INVALID")

    return errors


def heavy_state():
    heavy = resolve_heavy(ROOT)

    if heavy is None:
        return {
            "observed": False,
            "root": None,
            "writable": False,
        }

    return {
        "observed": True,
        "root": str(heavy),
        "writable": os.access(heavy, os.W_OK),
    }


def surface_state():
    return {
        "resolved_root": str(ROOT),
        "resolution": (
            "HOSTLESS_CORPUS_SIGNATURE"
            "+AUTHORITY_ROLE_MARKERS"
            "+HEAVY_MARKER_REJECTION"
        ),
        "AETHER": {
            "bind": "ONLY_BIND",
        },
        "AEUSB": {
            "observed": True,
            "root": str(ROOT),
            "authority": True,
            "forced_mount": False,
        },
        "AEXHD": heavy_state(),
        "runtime_env": {
            "AETHIEA_ROOT": os.environ.get("AETHIEA_ROOT"),
            "env_is_hint_only": True,
        },
    }


def scan_file(path):
    if path.name in EXCLUDE_FILES:
        return []

    if any(part in EXCLUDE_PARTS for part in path.parts):
        return []

    try:
        text = path.read_text(errors="ignore")
    except Exception:
        return []

    hits = []

    for expression, label in FORBIDDEN_PATTERNS:
        if expression.search(text):
            hits.append((label, str(path)))

    return hits


def scan_tree():
    hits = []

    for base in (
        ROOT / "CONFIG",
        ROOT / "SERVICES",
        ROOT / "TOOLIO/bin",
        ROOT / "DATA/RUNTIME",
    ):
        if not base.exists():
            continue

        for path in base.rglob("*"):
            if path.is_file():
                hits.extend(scan_file(path))

    return sorted(set(hits))


def resolve(surface):
    name = surface.upper()

    if name == "AETHER":
        return {
            "surface": "AETHER",
            "bind": "ONLY_BIND",
            "locator": "CONTINUITY_INTERFACE",
        }

    if name == "ROOT":
        return {
            "surface": "AETHIEAOPSYS",
            "root": str(ROOT),
            "resolution": "HOSTLESS_CORPUS_SIGNATURE",
        }

    if name == "AEUSB":
        return {
            "surface": "AEUSB",
            "root": str(ROOT),
            "authority": True,
            "state": "OBSERVED_BY_MARKERS_NO_FORCE_BIND",
            "forced_mount": False,
        }

    if name == "AEXHD":
        state = heavy_state()

        return {
            "surface": "AEXHD",
            **state,
            "authority": False,
            "locator": "HEAVY_MARKER_DISCOVERY",
        }

    if name == "AEVPS":
        return {
            "surface": "AEVPS",
            "alias": "aevps-001",
            "locator": "NETWORK_SURFACE_NOT_OWNER",
        }

    if name == "AERAG":
        return {
            "surface": "AERAG",
            "role": "MEMORY_PROOF_RETRIEVAL_CONTINUITY_ORGAN",
            "locator": "WITHIN_AETHIEAOPSYS_NOT_BODY",
        }

    if name == "VRAG":
        return {
            "surface": "vRAG",
            "role": "VECTOR_ENGINE_BENEATH_AERAG",
            "locator": "SUBORDINATE_IMPLEMENTATION",
        }

    return {
        "surface": name,
        "error": "UNKNOWN_SURFACE",
    }


def main(argv):
    command = argv[1] if len(argv) > 1 else "status"

    if command == "validate":
        errors = validate_policy(load_policy())

        print("POLICY_VALID" if not errors else "POLICY_INVALID")

        for error in errors:
            print(error)

        return 0 if not errors else 1

    if command == "status":
        errors = validate_policy(load_policy())

        print(
            json.dumps(
                {
                    "policy_valid": not errors,
                    "errors": errors,
                    "root": str(ROOT),
                    "lock": load_policy().get("lock"),
                    "bind_to": load_policy()
                    .get("policy", {})
                    .get("bind_to"),
                    "surface_state": surface_state(),
                },
                indent=2,
            )
        )

        return 0 if not errors else 1

    if command == "scan":
        hits = scan_tree()

        if hits:
            print("MECHANICAL_VIOLATIONS_FOUND")

            for label, path in hits:
                print(f"{label}\t{path}")

            return 2

        print("NO_MECHANICAL_VIOLATIONS")
        return 0

    if command == "resolve":
        target = argv[2] if len(argv) > 2 else "AETHER"
        print(json.dumps(resolve(target), indent=2))
        return 0

    raise SystemExit(f"unknown command: {command}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
