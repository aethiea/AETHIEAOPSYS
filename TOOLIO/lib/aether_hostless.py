#!/usr/bin/env python3

import glob
import json
import os
import sys
from pathlib import Path


SIGNATURE = Path(
    "CONFIG/authority/aether-corpus-signature.json"
)

POLICY = Path(
    "CONFIG/authority/aether-system-policy.json"
)

HEAVY_MARKERS = (
    ".aexhd_root",
    ".aeth_memory_body",
    ".aeth_heavy_body",
    "AE320GB_HEAVY_BODY",
)


def read_text(path: Path) -> str:
    try:
        return path.read_text(errors="replace").strip()
    except Exception:
        return ""


def ancestors(path: Path):
    resolved = path.expanduser().resolve()
    yield resolved
    yield from resolved.parents


def candidate_paths():
    seen = set()

    def emit(path):
        try:
            resolved = Path(path).expanduser().resolve()
        except Exception:
            return

        key = str(resolved)

        if key in seen:
            return

        seen.add(key)
        yield resolved

    # Environment values are hints only.
    for key in (
        "AETHIEA_ROOT",
        "AETH_ROOT",
        "AETHIEA",
        "AETHIEAOPSYS",
        "AEUSB",
        "AETHER_ROOT",
        "AE_ROOT",
    ):
        value = os.environ.get(key)

        if value:
            yield from emit(value)

    for path in ancestors(Path.cwd()):
        yield from emit(path)

    for path in ancestors(Path(__file__).resolve()):
        yield from emit(path)

    for pattern in (
        "/home/*/AETHIEAOPSYS",
        "/mnt/*/AETHIEAOPSYS",
        "/media/*/AETHIEAOPSYS",
        "/run/media/*/AETHIEAOPSYS",
        "/Volumes/*/AETHIEAOPSYS",
        "/opt/AETHIEAOPSYS",
    ):
        for raw in sorted(glob.glob(pattern)):
            yield from emit(raw)


def has_heavy_marker(root: Path) -> bool:
    return any(
        (root / marker).exists()
        for marker in HEAVY_MARKERS
    )


def load_controls(root: Path):
    signature_path = root / SIGNATURE
    policy_path = root / POLICY

    if not signature_path.is_file():
        return None

    if not policy_path.is_file():
        return None

    try:
        signature = json.loads(signature_path.read_text())
        policy = json.loads(policy_path.read_text())
    except Exception:
        return None

    return signature, policy


def valid_authority(root: Path):
    try:
        root = root.resolve()
    except Exception:
        return False, 0

    if not root.is_dir():
        return False, 0

    if not (root / ".aeth_root").is_file():
        return False, 0

    # Heavy storage may be a corpus member,
    # but it may never become ROOT authority.
    if has_heavy_marker(root):
        return False, 0

    surface = read_text(root / ".aeth_surface").upper()
    role = read_text(root / ".aeth_role").upper()

    if not (
        surface == "AEUSB"
        or "HOSTLESS_AUTHORITY" in role
    ):
        return False, 0

    controls = load_controls(root)

    if controls is None:
        return False, 0

    signature, policy = controls

    if signature.get("system") != "AETHIEAOPSYS":
        return False, 0

    if signature.get("bind_to") != "AETHER":
        return False, 0

    if signature.get("hostless") is not True:
        return False, 0

    if policy.get("lock") != (
        "BOUND_LESS_ONLY_BIND_TO_AETHER"
    ):
        return False, 0

    score = 1000

    for relative in (
        "CONFIG",
        "CORE",
        "DATA",
        "ENV/SURFACES/bootstrap.sh",
        "TOOLIO/bin",
    ):
        if (root / relative).exists():
            score += 10

    if os.access(root, os.R_OK):
        score += 5

    if os.access(root, os.W_OK):
        score += 5

    return True, score


def resolve_root() -> Path:
    best_root = None
    best_score = -1

    # Equal scores preserve discovery order.
    # Path spelling is never an authority tiebreaker.
    for candidate in candidate_paths():
        valid, score = valid_authority(candidate)

        if not valid:
            continue

        if score > best_score:
            best_root = candidate.resolve()
            best_score = score

    if best_root is None:
        raise SystemExit(
            "NO_HOSTLESS_AEUSB_AUTHORITY_FOUND"
        )

    return best_root


def heavy_candidates():
    seen = set()

    values = []

    for key in (
        "AEXHD_ROOT",
        "AEHEAVY_ROOT",
        "AE320",
    ):
        value = os.environ.get(key)

        if value:
            values.append(value)

    for pattern in (
        "/mnt/*/AETHIEAOPSYS",
        "/media/*/AETHIEAOPSYS",
        "/run/media/*/AETHIEAOPSYS",
        "/Volumes/*/AETHIEAOPSYS",
        "/srv/AETHIEAOPSYS_HEAVY/AETHIEAOPSYS",
    ):
        values.extend(sorted(glob.glob(pattern)))

    for raw in values:
        try:
            path = Path(raw).expanduser().resolve()
        except Exception:
            continue

        key = str(path)

        if key in seen:
            continue

        seen.add(key)
        yield path


def resolve_heavy(authority=None):
    authority = (
        authority.resolve()
        if authority is not None
        else resolve_root()
    )

    for candidate in heavy_candidates():
        if candidate == authority:
            continue

        if not candidate.is_dir():
            continue

        if has_heavy_marker(candidate):
            return candidate

    return None


def status_payload():
    root = resolve_root()
    heavy = resolve_heavy(root)

    return {
        "resolved_root": str(root),
        "resolution": (
            "HOSTLESS_CORPUS_SIGNATURE"
            "+AUTHORITY_ROLE_MARKERS"
            "+HEAVY_MARKER_REJECTION"
        ),
        "authority": {
            "surface": read_text(
                root / ".aeth_surface"
            ),
            "role": read_text(
                root / ".aeth_role"
            ),
            "root_marker": str(
                root / ".aeth_root"
            ),
        },
        "bind_to": "AETHER",
        "host_bind": False,
        "heavy_root": (
            str(heavy)
            if heavy is not None
            else None
        ),
        "env_AETHIEA_ROOT": os.environ.get(
            "AETHIEA_ROOT"
        ),
        "env_is_hint_only": True,
    }


def main():
    command = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "root"
    )

    if command == "root":
        print(resolve_root())
        return 0

    if command == "heavy":
        heavy = resolve_heavy()

        if heavy is None:
            print("AEXHD_OFFLINE")
            return 1

        print(heavy)
        return 0

    if command == "status":
        print(
            json.dumps(
                status_payload(),
                indent=2,
            )
        )
        return 0

    raise SystemExit(
        f"unknown command: {command}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
