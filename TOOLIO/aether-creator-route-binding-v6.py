#!/usr/bin/env python3
"""Fix the V4/V5 AETHER auto-route run_code_task binding.

The live CLI already routes inspection/reuse implementation requests correctly,
but main() has an existing local binding/import for run_code_task. Because the
auto-route executes before that binding, calling run_code_task directly raises
UnboundLocalError. This patch gives only the auto-route its own immediately
bound alias and leaves the existing /code* handlers unchanged.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path("/opt/AETHIEAOPSYS")
BODY = ROOT / "WORKSPACE/codex/aether-chat-aevps"
CLI = BODY / "body/cli.py"
STATE = ROOT / "STATE/aetherbot/creator-route-binding"

EXPECTED_CLI_SHA256 = "446e6b0b4c78a60c1cfa53dbda5bb70986d3fdeb16787c4656a923c0f9852d16"
ROUTE_MARKER = "# AETHER_CREATOR_AUTO_ROUTE_V4"
ROUTE_BANNER = 'print("CODE ROUTE → AUTO // REUSE-FIRST")'
ALIAS_IMPORT = "from .code_engine import run_code_task as _aether_auto_run_code_task"
OLD_CALL = "rc = run_code_task("
NEW_CALL = "rc = _aether_auto_run_code_task("
PATCH_MARKER = "# AETHER_CREATOR_ROUTE_BINDING_V6"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_candidate(source: str) -> str:
    if PATCH_MARKER in source and ALIAS_IMPORT in source and NEW_CALL in source:
        return source

    if ROUTE_MARKER not in source:
        raise RuntimeError("V4_ROUTE_MARKER_MISSING")

    lines = source.splitlines(keepends=True)
    banner_indexes = [i for i, line in enumerate(lines) if ROUTE_BANNER in line]
    if len(banner_indexes) != 1:
        raise RuntimeError(f"AUTO_ROUTE_BANNER_COUNT={len(banner_indexes)}")

    banner_i = banner_indexes[0]
    call_i = None
    for i in range(banner_i + 1, min(len(lines), banner_i + 16)):
        if OLD_CALL in lines[i]:
            call_i = i
            break
        if NEW_CALL in lines[i]:
            call_i = i
            break

    if call_i is None:
        raise RuntimeError("AUTO_ROUTE_CALL_NOT_FOUND_NEAR_BANNER")

    stripped = lines[call_i].lstrip()
    indent = lines[call_i][: len(lines[call_i]) - len(stripped)]

    if NEW_CALL in lines[call_i]:
        if not any(ALIAS_IMPORT in lines[i] for i in range(banner_i, call_i + 1)):
            lines.insert(call_i, f"{indent}{ALIAS_IMPORT}\n")
        return "".join(lines)

    if OLD_CALL not in lines[call_i]:
        raise RuntimeError("AUTO_ROUTE_CALL_UNEXPECTED")

    lines[call_i] = lines[call_i].replace(OLD_CALL, NEW_CALL, 1)
    lines.insert(call_i, f"{indent}{PATCH_MARKER}\n{indent}{ALIAS_IMPORT}\n")
    return "".join(lines)


def compile_file(path: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "py_compile", str(path)],
        cwd=str(BODY),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return proc.returncode, proc.stdout.rstrip()


def main() -> int:
    if os.geteuid() != 0:
        print("STOP=ROOT_REQUIRED")
        return 2
    if not CLI.is_file():
        print("STOP=CLI_MISSING")
        return 3

    current_hash = sha256(CLI)
    source = CLI.read_text(encoding="utf-8")

    print("AETHER CREATOR // ROUTE BINDING V6")
    print(f"CLI={CLI}")
    print(f"CLI_SHA256={current_hash}")
    print(f"EXPECTED_CLI_SHA256={EXPECTED_CLI_SHA256}")
    print(f"V4_ROUTE_PRESENT={'YES' if ROUTE_MARKER in source else 'NO'}")
    print(f"V6_BINDING_PRESENT={'YES' if PATCH_MARKER in source else 'NO'}")
    print("CREATOR_ENGINE_CHANGED=NO")
    print("OPEN_PROMPT_CHANGED=NO")
    print("MODEL_CHANGED=NO")
    print("MIDDLEWARE_CHANGED=NO")
    print("EXECUTOR_CHANGED=NO")
    print("PATH_SCOPE_CHANGED=NO")
    print("RECEIPTS_CHANGED=NO")

    if PATCH_MARKER in source and ALIAS_IMPORT in source and NEW_CALL in source:
        print("AETHER_CREATOR_ROUTE_BINDING=ALREADY_V6")
        return 0

    if current_hash != EXPECTED_CLI_SHA256:
        print("STOP=UNEXPECTED_CLI_SHA256")
        print(f"EXPECTED={EXPECTED_CLI_SHA256}")
        print(f"ACTUAL={current_hash}")
        return 4

    try:
        candidate = build_candidate(source)
        compile(candidate, str(CLI), "exec")
    except Exception as exc:
        print(f"STOP=CANDIDATE_BUILD:{exc}")
        return 5

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    backup_dir = STATE / stamp
    backup_dir.mkdir(parents=True, exist_ok=False)
    backup = backup_dir / "cli.py.before"
    candidate_path = backup_dir / "cli.py.candidate"

    shutil.copy2(CLI, backup)
    candidate_path.write_text(candidate, encoding="utf-8")

    rc, output = compile_file(candidate_path)
    if rc:
        print("STOP=CANDIDATE_COMPILE_FAILED")
        print(output)
        return 6

    CLI.write_text(candidate, encoding="utf-8")
    rc, output = compile_file(CLI)
    if rc:
        shutil.copy2(backup, CLI)
        print("ROLLBACK=LIVE_COMPILE_FAILED")
        print(output)
        return 7

    final = CLI.read_text(encoding="utf-8")
    checks = {
        "V4_ROUTE": ROUTE_MARKER in final,
        "V6_BINDING": PATCH_MARKER in final,
        "ALIAS_IMPORT": ALIAS_IMPORT in final,
        "ALIAS_CALL": NEW_CALL in final,
        "ROUTE_BANNER": ROUTE_BANNER in final,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        shutil.copy2(backup, CLI)
        print("ROLLBACK=VERIFY_FAILED:" + ",".join(failed))
        return 8

    print("AETHER_CREATOR_ROUTE_BINDING=V6")
    print("AUTO_ROUTE_LOCAL_BINDING=FIXED")
    print("EXPLICIT_CODE_HANDLERS=UNCHANGED")
    print("REUSE_FIRST_ENGINE=UNCHANGED")
    print("CLI_COMPILE=PASS")
    print(f"CLI_SHA256_NEW={sha256(CLI)}")
    print(f"BACKUP_DIR={backup_dir}")
    return 0


raise SystemExit(main())
