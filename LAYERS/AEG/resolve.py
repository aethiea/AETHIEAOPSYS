#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_config() -> dict[str, Any]:
    path = Path(__file__).with_name("config.json")
    return json.loads(path.read_text(encoding="utf-8"))


def windows_volumes() -> list[dict[str, str]]:
    command = r'''
$ErrorActionPreference = "Stop"
Get-Volume |
Where-Object { $_.DriveLetter } |
ForEach-Object {
  "{0}|{1}|{2}|{3}|{4}" -f
    $_.DriveLetter,
    $_.FileSystemLabel,
    $_.FileSystem,
    $_.HealthStatus,
    $_.UniqueId
}
'''
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []

    records: list[dict[str, str]] = []
    for raw in result.stdout.replace("\r", "").splitlines():
        parts = raw.split("|", 4)
        if len(parts) != 5:
            continue
        letter, label, filesystem, health, unique_id = parts
        records.append(
            {
                "letter": letter.strip(),
                "label": label.strip(),
                "filesystem": filesystem.strip(),
                "health": health.strip(),
                "unique_id": unique_id.strip(),
            }
        )
    return records


def read_marker(path: Path) -> str | None:
    if not path.is_file():
        return None

    try:
        return path.read_text(
            encoding="utf-8",
            errors="replace",
        ).strip()
    except OSError:
        return None


def marker_role(corpus: Path) -> str | None:
    root_marker = corpus / ".aeth_root"
    role_marker = corpus / ".aeth_role"
    surface_marker = corpus / ".aeth_surface"

    if not (
        root_marker.is_file()
        and role_marker.is_file()
        and surface_marker.is_file()
    ):
        return None

    role_text = read_marker(role_marker)
    surface_text = read_marker(surface_marker)

    if role_text is None or surface_text is None:
        return None

    detected: set[str] = set()
    surface_upper = surface_text.upper()
    role_upper = role_text.upper()

    if surface_upper in {"AEUSB", "AEXHD"}:
        detected.add(surface_upper)

    for role in ("AEUSB", "AEXHD"):
        if role in role_upper:
            detected.add(role)

    if len(detected) != 1:
        return None

    return next(iter(detected))


def corroborated_role(
    corpus: Path,
    label_role: str | None,
) -> str | None:
    role = marker_role(corpus)

    if role is None:
        return None

    if label_role is not None and label_role != role:
        return None

    heavy_markers = (
        corpus / ".aeth_heavy_body",
        corpus / "AE320GB_HEAVY_BODY",
    )

    if role == "AEUSB" and any(
        marker.exists()
        for marker in heavy_markers
    ):
        return None

    return role


def resolve() -> dict[str, Any]:
    config = load_config()
    labels = config["label_roles"]
    candidates: list[dict[str, Any]] = []

    for volume in windows_volumes():
        letter = volume["letter"]
        if not letter:
            continue

        corpus = Path("/mnt") / letter.casefold() / config["corpus_directory"]
        if not corpus.is_dir():
            continue

        role = corroborated_role(
            corpus,
            labels.get(volume["label"]),
        )
        if role not in {"AEUSB", "AEXHD"}:
            continue

        candidates.append(
            {
                "role": role,
                "current_root": str(corpus),
                "current_mount": str(corpus.parent),
                "mount_ephemeral": True,
                "volume_label": volume["label"],
                "filesystem": volume["filesystem"],
                "health": volume["health"],
                "unique_id": volume["unique_id"],
                "markers": {
                    ".aeth_root": (corpus / ".aeth_root").is_file(),
                    ".aeth_role": (corpus / ".aeth_role").is_file(),
                    ".aeth_surface": (corpus / ".aeth_surface").is_file(),
                },
            }
        )

    roles: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []

    for candidate in candidates:
        role = candidate["role"]
        if role in roles:
            duplicates.append(role)
        else:
            roles[role] = candidate

    return {
        "schema": "aethiea.aeg.body-resolution.v1",
        "canonical_name": "AEGNOSTIXXX",
        "utc": utc_now(),
        "mount_path_is_identity": False,
        "drive_letter_is_identity": False,
        "duplicates": sorted(set(duplicates)),
        "roles": roles,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exports", action="store_true")
    parser.add_argument("--require", default="AEUSB,AEXHD")
    args = parser.parse_args()

    result = resolve()
    required = [item.strip() for item in args.require.split(",") if item.strip()]
    missing = [role for role in required if role not in result["roles"]]

    if result["duplicates"] or missing:
        print(
            json.dumps(
                {
                    **result,
                    "state": "FAIL",
                    "missing": missing,
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2

    result["state"] = "PASS"

    if args.exports:
        for role in required:
            value = result["roles"][role]["current_root"]
            print(f"export {role}_ROOT={shlex.quote(value)}")
        print("export AEGNOSTIXXX_RESOLUTION=PASS")
    else:
        print(json.dumps(result, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
