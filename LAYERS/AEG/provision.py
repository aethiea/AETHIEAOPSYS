#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


PROFILES: dict[str, dict[str, str]] = {
    "AEUSB": {
        "surface": "AEUSB",
        "role": "HOSTLESS_AUTHORITY",
    },
    "AEXHD": {
        "surface": "AEXHD",
        "role": "MIRROR_CONTINUITY+HEAVY_PAYLOAD_BODY",
    },
}

HEAVY_MARKERS = (
    ".aeth_heavy_body",
    "AE320GB_HEAVY_BODY",
)


def emit(
    payload: dict[str, Any],
    *,
    stderr: bool = False,
) -> None:
    print(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        ),
        file=sys.stderr if stderr else sys.stdout,
    )


def reject(
    payload: dict[str, Any],
    message: str,
    *,
    code: int,
    state: str = "REJECTED",
) -> int:
    payload["state"] = state
    payload["error"] = message
    emit(payload, stderr=True)
    return code


def read_config(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(
            encoding="utf-8",
            errors="strict",
        )
    )


def read_marker(path: Path) -> str:
    return path.read_text(
        encoding="utf-8",
        errors="strict",
    ).strip()


def exclusive_create(
    path: Path,
    value: str,
) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600,
    )

    try:
        payload = (value + "\n").encode("utf-8")

        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Provision missing AEG role metadata on an already "
            "established corpus body. Dry-run is the default."
        )
    )

    parser.add_argument(
        "--root",
        required=True,
        help="Existing AETHIEAOPSYS corpus directory",
    )

    parser.add_argument(
        "--role",
        required=True,
        choices=tuple(PROFILES),
        help="Established logical body role",
    )

    parser.add_argument(
        "--config",
        default=str(
            Path(__file__).with_name("config.json")
        ),
        help="AEG configuration file",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Create approved missing role metadata",
    )

    args = parser.parse_args()

    result: dict[str, Any] = {
        "schema": "aethiea.aeg.provision-result.v1",
        "role": args.role,
        "apply": args.apply,
        "creates_authority": False,
        "preexisting_root_marker_required": True,
        "heavy_topology_created": False,
        "mount_path_is_identity": False,
    }

    try:
        root = Path(args.root).expanduser().resolve(
            strict=True
        )
    except (FileNotFoundError, OSError) as exc:
        return reject(
            result,
            f"ROOT_UNAVAILABLE:{exc}",
            code=2,
        )

    result["root"] = str(root)

    if not root.is_dir():
        return reject(
            result,
            f"ROOT_NOT_DIRECTORY:{root}",
            code=2,
        )

    config_path = Path(args.config).expanduser()

    try:
        config = read_config(config_path)
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
    ) as exc:
        return reject(
            result,
            f"CONFIG_UNAVAILABLE:{exc}",
            code=2,
        )

    expected_directory = config.get(
        "corpus_directory"
    )

    if (
        not isinstance(expected_directory, str)
        or not expected_directory
    ):
        return reject(
            result,
            "CONFIG_CORPUS_DIRECTORY_INVALID",
            code=2,
        )

    if root.name != expected_directory:
        return reject(
            result,
            (
                "CORPUS_DIRECTORY_NAME_MISMATCH:"
                f"expected={expected_directory}:"
                f"actual={root.name}"
            ),
            code=2,
        )

    root_marker = root / ".aeth_root"

    if not root_marker.is_file():
        return reject(
            result,
            f"PREEXISTING_ROOT_MARKER_REQUIRED:{root_marker}",
            code=2,
        )

    heavy_present: list[str] = []

    for marker_name in HEAVY_MARKERS:
        marker_path = root / marker_name

        if not marker_path.exists():
            continue

        if not marker_path.is_file():
            return reject(
                result,
                f"HEAVY_MARKER_NOT_FILE:{marker_name}",
                code=2,
            )

        heavy_present.append(marker_name)

    if args.role == "AEUSB" and heavy_present:
        return reject(
            result,
            (
                "AEUSB_CANNOT_CARRY_HEAVY_MARKERS:"
                + ",".join(heavy_present)
            ),
            code=2,
        )

    if args.role == "AEXHD" and not heavy_present:
        return reject(
            result,
            "AEXHD_REQUIRES_PREEXISTING_HEAVY_MARKER",
            code=2,
        )

    profile = PROFILES[args.role]

    expected_markers = {
        ".aeth_role": profile["role"],
        ".aeth_surface": profile["surface"],
    }

    planned: list[dict[str, str]] = []
    conflicts: list[dict[str, str]] = []

    for marker_name, expected_value in (
        expected_markers.items()
    ):
        marker_path = root / marker_name

        if not marker_path.exists():
            planned.append(
                {
                    "marker": marker_name,
                    "value": expected_value,
                }
            )
            continue

        if not marker_path.is_file():
            conflicts.append(
                {
                    "marker": marker_name,
                    "reason": "NOT_A_REGULAR_FILE",
                    "expected": expected_value,
                }
            )
            continue

        try:
            actual_value = read_marker(marker_path)
        except (OSError, UnicodeError) as exc:
            conflicts.append(
                {
                    "marker": marker_name,
                    "reason": f"UNREADABLE:{exc}",
                    "expected": expected_value,
                }
            )
            continue

        if actual_value != expected_value:
            conflicts.append(
                {
                    "marker": marker_name,
                    "reason": "VALUE_CONFLICT",
                    "actual": actual_value,
                    "expected": expected_value,
                }
            )

    result["planned_writes"] = planned
    result["conflicts"] = conflicts

    if conflicts:
        result["state"] = "CONFLICT"
        emit(result, stderr=True)
        return 3

    if not planned:
        result["state"] = "ALREADY_PROVISIONED"
        emit(result)
        return 0

    if not args.apply:
        result["state"] = "DRY_RUN"
        emit(result)
        return 0

    created: list[Path] = []

    try:
        for item in planned:
            marker_path = root / item["marker"]

            exclusive_create(
                marker_path,
                item["value"],
            )

            created.append(marker_path)
    except OSError as exc:
        for marker_path in reversed(created):
            try:
                marker_path.unlink()
            except OSError:
                pass

        result["created_before_rollback"] = [
            path.name
            for path in created
        ]

        return reject(
            result,
            f"WRITE_FAILED_ROLLED_BACK:{exc}",
            code=4,
            state="WRITE_FAILURE",
        )

    post_errors: list[str] = []

    for marker_name, expected_value in (
        expected_markers.items()
    ):
        marker_path = root / marker_name

        if not marker_path.is_file():
            post_errors.append(
                f"MISSING_AFTER_WRITE:{marker_name}"
            )
            continue

        try:
            actual_value = read_marker(marker_path)
        except (OSError, UnicodeError) as exc:
            post_errors.append(
                f"UNREADABLE_AFTER_WRITE:"
                f"{marker_name}:{exc}"
            )
            continue

        if actual_value != expected_value:
            post_errors.append(
                f"VALUE_MISMATCH_AFTER_WRITE:"
                f"{marker_name}"
            )

    if post_errors:
        result["state"] = "POST_WRITE_VALIDATION_FAILED"
        result["post_errors"] = post_errors
        emit(result, stderr=True)
        return 5

    result["state"] = "APPLIED"
    result["created"] = [
        path.name
        for path in created
    ]

    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
