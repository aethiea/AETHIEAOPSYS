#!/usr/bin/env python3
"""Minimize the AETHER OPEN conversational system membrane.

This patch intentionally changes only OPEN_SYSTEM in the live AETHER service.
It does not alter GROUND/OPS routing, vRAG, AEMCP, B43, secrets handling,
systemd hardening, filesystem permissions, or execution/tool boundaries.

Fail-closed contract:
- apply only to the currently observed live source hash unless already patched;
- create a timestamped backup before replacement;
- compile the complete candidate source before install;
- restart only aether.service and verify its loopback health endpoint.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path("/opt/AETHIEAOPSYS")
TARGET = ROOT / "WORKSPACE/codex/aether-chat-aevps/src/aether_chat.py"
STATE = ROOT / "STATE/aetherbot/open-membrane"
EXPECTED_SHA256 = "b47a0b3c8302fe3789383a420e805b086241bc0bfbf43a1f312050f050003fac"
MARKER = "# AETHER_OPEN_MEMBRANE_MINIMAL_V1"

NEW_OPEN_BLOCK = '''# AETHER_OPEN_MEMBRANE_MINIMAL_V1
OPEN_SYSTEM = """\\
You are AETHER, the local conversational intelligence of AETHIEAOPSYS.

OPEN CHAT MODE:

Converse directly and naturally with the operator.
Use relevant conversation history naturally.
Answer at the level of detail, tone, and technical depth the operator asks for.
Do not inject policy, compliance, governance, audit, topology, routing, or evidence boilerplate unless the operator explicitly asks for it or the subject itself requires it.
Do not invent tool execution, retrieval, or live system actions that did not actually occur.
"""


'''


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def build_candidate(source: str) -> str:
    start_token = 'OPEN_SYSTEM = """\\\n'
    end_token = 'GROUND_SYSTEM = """\\\n'

    start = source.find(start_token)
    if start < 0:
        raise RuntimeError("OPEN_SYSTEM_START_NOT_FOUND")

    ground = source.find(end_token, start + len(start_token))
    if ground < 0:
        raise RuntimeError("GROUND_SYSTEM_START_NOT_FOUND")

    # Keep the GROUND_SYSTEM assignment itself; replace only the complete OPEN
    # block and any whitespace immediately before GROUND_SYSTEM.
    return source[:start] + NEW_OPEN_BLOCK + source[ground:]


def health_ok() -> bool:
    for _ in range(40):
        cp = subprocess.run(
            ["curl", "-fsS", "http://127.0.0.1:3936/health"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if cp.returncode == 0:
            return True
        time.sleep(0.5)
    return False


def plan() -> int:
    if not TARGET.is_file():
        print(f"STOP=TARGET_MISSING:{TARGET}")
        return 2

    current = sha256(TARGET)
    text = TARGET.read_text(encoding="utf-8")
    print("AETHER OPEN MEMBRANE // PLAN")
    print(f"TARGET={TARGET}")
    print(f"CURRENT_SHA256={current}")
    print(f"EXPECTED_PREPATCH_SHA256={EXPECTED_SHA256}")
    print(f"ALREADY_PATCHED={'YES' if MARKER in text else 'NO'}")
    print("OPEN_SYSTEM_ONLY=YES")
    print("GROUND_CHANGED=NO")
    print("OPS_CHANGED=NO")
    print("AEMCP_CHANGED=NO")
    print("VRAG_CHANGED=NO")
    print("B43_CHANGED=NO")
    print("EXECUTION_SANDBOX_CHANGED=NO")
    print("SYSTEMD_HARDENING_CHANGED=NO")
    return 0


def apply() -> int:
    if os.geteuid() != 0:
        print("STOP=ROOT_REQUIRED")
        return 2
    if not TARGET.is_file():
        print(f"STOP=TARGET_MISSING:{TARGET}")
        return 2

    original = TARGET.read_text(encoding="utf-8")
    current = sha256(TARGET)

    if MARKER in original:
        print("OPEN_MEMBRANE=ALREADY_PATCHED")
        print(f"CURRENT_SHA256={current}")
        return 0

    if current != EXPECTED_SHA256:
        print("STOP=SOURCE_HASH_CHANGED")
        print(f"CURRENT_SHA256={current}")
        print(f"EXPECTED_SHA256={EXPECTED_SHA256}")
        return 3

    try:
        candidate = build_candidate(original)
    except RuntimeError as exc:
        print(f"STOP={exc}")
        return 4

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    backup_dir = STATE / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / "aether_chat.py.before"
    shutil.copy2(TARGET, backup)

    candidate_path = backup_dir / "aether_chat.py.candidate"
    candidate_path.write_text(candidate, encoding="utf-8")

    cp = subprocess.run(
        [sys.executable, "-m", "py_compile", str(candidate_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if cp.returncode != 0:
        print("STOP=CANDIDATE_COMPILE_FAILED")
        print(cp.stderr.rstrip())
        return 5

    temp = TARGET.with_suffix(".py.open-membrane-new")
    temp.write_text(candidate, encoding="utf-8")
    os.chmod(temp, TARGET.stat().st_mode)
    os.replace(temp, TARGET)

    subprocess.run([sys.executable, "-m", "py_compile", str(TARGET)], check=True)
    subprocess.run(["systemctl", "restart", "aether.service"], check=True)

    if not health_ok():
        shutil.copy2(backup, TARGET)
        subprocess.run([sys.executable, "-m", "py_compile", str(TARGET)], check=False)
        subprocess.run(["systemctl", "restart", "aether.service"], check=False)
        print("ROLLBACK=AETHER_HEALTH_FAILED")
        return 6

    print("OPEN_MEMBRANE=MINIMAL_V1")
    print(f"NEW_SHA256={sha256(TARGET)}")
    print("AETHER_3936=ONLINE")
    print("MODEL_POLICY_BOILERPLATE=REMOVED_FROM_OPEN")
    print("EXECUTION_SANDBOX_CHANGED=NO")
    print("SYSTEMD_HARDENING_CHANGED=NO")
    print("GROUND_CHANGED=NO")
    print("OPS_CHANGED=NO")
    print("AEMCP_CHANGED=NO")
    print("VRAG_CHANGED=NO")
    print("B43_CHANGED=NO")
    print(f"BACKUP={backup}")
    return 0


def rollback() -> int:
    if os.geteuid() != 0:
        print("STOP=ROOT_REQUIRED")
        return 2
    backups = sorted(STATE.glob("*/aether_chat.py.before"), reverse=True)
    if not backups:
        print("STOP=NO_BACKUP_FOUND")
        return 3
    backup = backups[0]
    shutil.copy2(backup, TARGET)
    subprocess.run([sys.executable, "-m", "py_compile", str(TARGET)], check=True)
    subprocess.run(["systemctl", "restart", "aether.service"], check=True)
    if not health_ok():
        print("STOP=ROLLBACK_HEALTH_FAILED")
        return 4
    print(f"ROLLBACK=PASS:{backup}")
    print(f"CURRENT_SHA256={sha256(TARGET)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true")
    group.add_argument("--rollback", action="store_true")
    args = parser.parse_args()
    if args.apply:
        return apply()
    if args.rollback:
        return rollback()
    return plan()


if __name__ == "__main__":
    raise SystemExit(main())
