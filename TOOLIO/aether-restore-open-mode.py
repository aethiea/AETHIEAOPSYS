#!/usr/bin/env python3

"""Restore the historically proven AETHER open-mode source set from local backups.

This utility is intentionally fail-closed. It never reconstructs source from guesses.
It searches the live AEVPS workspace for byte-for-byte files matching the known-good
post-open-mode SHA256 values captured on 2026-08-31. All four files must be found and
compile together before any live file is replaced.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path("/opt/AETHIEAOPSYS").resolve()
WS = ROOT / "WORKSPACE" / "codex" / "aether-chat-aevps"
STATE = ROOT / "STATE" / "aetherbot" / "open-mode-restore"
AETHER_URL = "http://127.0.0.1:3936/health"

TARGETS = {
    WS / "src" / "aether_chat.py": "b2f3919645143377d792649f604f106619304b1f317383f039a19ac26f54f46b",
    WS / "body" / "chat.py": "36fe9c8f204589401221f3662fcd31487337b1c2c31c8c6dd6a576ddaf3d9b4c",
    WS / "body" / "session.py": "4a8405356e11e759883540c5f5b6d3c6b5b24527de2b78cddbb36f412d1dc626",
    WS / "body" / "cli.py": "7cd6fd8f744a382488abbf7f2767ceabcd449a354cafd8dc6b09dc7aebadd716",
}

SIGNATURES = {
    "aether_chat.py": ("CHAT_MODES", "OPEN_SYSTEM", "GROUND_SYSTEM", "requested_mode"),
    "chat.py": ('self.session.mode == "open"', '"mode":'),
    "session.py": ('mode: str = "open"', '"mode":'),
    "cli.py": ('if message == "/open"', '"mode=open"'),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(argv: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=check,
    )


def candidate_paths(target: Path) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []

    def add(path: Path) -> None:
        try:
            resolved = path.resolve()
        except OSError:
            return
        if resolved in seen or not resolved.is_file():
            return
        seen.add(resolved)
        out.append(resolved)

    add(target)
    if target.parent.exists():
        for path in target.parent.glob(target.name + "*"):
            add(path)

    # Historical patches stored .pre-* copies beside the source. Search the
    # canonical AETHER workspace only; do not roam the whole filesystem.
    if WS.exists():
        for path in WS.rglob(target.name + "*"):
            add(path)

    out.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return out


def locate_exact(target: Path, expected: str) -> Path | None:
    for path in candidate_paths(target):
        try:
            if sha256(path) == expected:
                return path
        except OSError:
            continue
    return None


def verify_signatures(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="strict")
    missing = [token for token in SIGNATURES[path.name] if token not in text]
    if missing:
        raise RuntimeError(f"signature check failed for {path}: missing {missing}")


def compile_set(paths: list[Path]) -> None:
    result = run(["python3", "-m", "py_compile", *map(str, paths)], check=False)
    if result.returncode != 0:
        raise RuntimeError("candidate compile failed:\n" + result.stdout)


def health_ok() -> bool:
    try:
        with urllib.request.urlopen(AETHER_URL, timeout=2) as response:
            return response.status == 200
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="install the exact historical set")
    args = parser.parse_args()

    if not WS.is_dir():
        print(f"STOP=AETHER_WORKSPACE_MISSING:{WS}")
        return 2

    print("=== AETHER OPEN-MODE RESTORE DISCOVERY ===")
    selected: dict[Path, Path] = {}

    for target, expected in TARGETS.items():
        current = sha256(target) if target.is_file() else "MISSING"
        match = locate_exact(target, expected)
        print(f"target={target}")
        print(f"current_sha256={current}")
        print(f"expected_sha256={expected}")
        print(f"exact_match={match if match else 'NOT_FOUND'}")
        if match is None:
            print("STOP=EXACT_HISTORICAL_SET_INCOMPLETE")
            return 3
        selected[target] = match

    staged = STATE / "staged"
    if staged.exists():
        shutil.rmtree(staged)
    staged.mkdir(parents=True, exist_ok=True)

    staged_paths: list[Path] = []
    for target, source in selected.items():
        dest = staged / target.relative_to(WS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        if sha256(dest) != TARGETS[target]:
            raise RuntimeError(f"staged hash changed for {target}")
        verify_signatures(dest)
        staged_paths.append(dest)

    compile_set(staged_paths)
    print("CANDIDATE_COMPILE=PASS")
    print("STATIC_OPEN_MODE_SIGNATURES=PASS")

    if not args.apply:
        print("MUTATION_PERFORMED=NO")
        print("NEXT=rerun_with_--apply")
        return 0

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = STATE / "backups" / stamp
    backup_root.mkdir(parents=True, exist_ok=True)

    # Back up every current target before the first replacement.
    for target in TARGETS:
        if target.is_file():
            backup = backup_root / target.relative_to(WS)
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup)

    try:
        for target in TARGETS:
            staged_file = staged / target.relative_to(WS)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(staged_file, target)

        live_paths = list(TARGETS)
        compile_set(live_paths)
        for target, expected in TARGETS.items():
            actual = sha256(target)
            if actual != expected:
                raise RuntimeError(f"post-install hash mismatch: {target}: {actual}")

        restart = run(["systemctl", "restart", "aether.service"], check=False)
        if restart.returncode != 0:
            raise RuntimeError("aether.service restart failed:\n" + restart.stdout)

        for _ in range(30):
            if health_ok():
                break
            time.sleep(1)
        else:
            raise RuntimeError("AETHER :3936 health did not recover")

    except Exception:
        print("RESTORE_FAILED=YES")
        print("ROLLBACK=START")
        for target in TARGETS:
            backup = backup_root / target.relative_to(WS)
            if backup.is_file():
                shutil.copy2(backup, target)
        run(["systemctl", "restart", "aether.service"], check=False)
        raise

    print("=== RESTORED ===")
    for target, expected in TARGETS.items():
        print(f"{target.name}_sha256={sha256(target)}")
        print(f"{target.name}_expected={expected}")
    print("AETHER_OPEN_MODE_SOURCE_SET=RESTORED")
    print("AETHER_3936=ONLINE")
    print(f"BACKUP_ROOT={backup_root}")
    print("B43_RESTARTED=NO")
    print("LLAMA_RESTARTED=NO")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR={type(exc).__name__}:{exc}", file=sys.stderr)
        raise
