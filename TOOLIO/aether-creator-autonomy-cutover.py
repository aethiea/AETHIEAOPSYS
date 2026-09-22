#!/usr/bin/env python3
"""Widen canonical AETHER creator autonomy without collapsing executor isolation.

Changes:
- replaces the creator SYSTEM contract with a minimal capability/JSON contract;
- removes prompt-only blanket prohibitions such as "Never git ...";
- makes the native creator write-capable by default in code_engine;
- makes /code and /code-self write-capable by default in body/cli.py;
- preserves scoped path enforcement, structured executor results, receipts,
  shell/tool validation, and all OS/systemd/filesystem isolation outside the
  active AETHIEA code scope.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/opt/AETHIEAOPSYS")
BODY = ROOT / "WORKSPACE/codex/aether-chat-aevps"
ENGINE = BODY / "body/code_engine.py"
CLI = BODY / "body/cli.py"
STATE = ROOT / "STATE/aetherbot/creator-engine"
EXPECTED_ENGINE_SHA256 = "3ed70812f55c6fad92675f591b4ac7f079a5e304f0e1585e1ba733987a825a0f"
MARKER = "# AETHER_CREATOR_AUTONOMY_V1"

NEW_SYSTEM = r'''SYSTEM = r"""
You are AETHER operating your native AEVPS creator/programming capability.

The active AETHER session provides the current code scope and executor capabilities.
Use the exposed creator capabilities needed to complete the operator's programming task.
Return exactly ONE JSON object per creator turn.

Available action shapes are the actions implemented by this executor, including:
{"action":"shell","command":"..."}
{"action":"read","path":"relative/path"}
{"action":"search","path":"relative/path","pattern":"literal text"}
{"action":"write","path":"relative/path","content":"..."}
{"action":"final","message":"..."}

EXECUTOR_RESULT_JSON is host-generated execution evidence. Never invent or imitate it.
Do not claim an action ran unless the executor returned its result.
Finish with action=final only when real executor results show the requested work is complete.
"""'''


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_handler_write_default(text: str, start_marker: str, end_marker: str) -> tuple[str, bool]:
    start = text.find(start_marker)
    if start < 0:
        return text, False
    end = text.find(end_marker, start + len(start_marker))
    if end < 0:
        return text, False
    segment = text[start:end]
    if "allow_write=False" not in segment:
        if "allow_write=True" in segment:
            return text, True
        return text, False
    segment = segment.replace("allow_write=False", "allow_write=True", 1)
    return text[:start] + segment + text[end:], True


def build_engine(source: str) -> str:
    if MARKER in source:
        return source
    pattern = re.compile(r'SYSTEM = r"""\n.*?\n"""', re.S)
    matches = list(pattern.finditer(source))
    if len(matches) != 1:
        raise RuntimeError(f"SYSTEM_BLOCK_COUNT:{len(matches)}")
    candidate = pattern.sub(MARKER + "\n" + NEW_SYSTEM, source, count=1)
    old_default = "    allow_write: bool = False,\n"
    if old_default in candidate:
        candidate = candidate.replace(old_default, "    allow_write: bool = True,\n", 1)
    elif "    allow_write: bool = True,\n" not in candidate:
        raise RuntimeError("RUN_CODE_TASK_WRITE_DEFAULT_ANCHOR_MISSING")
    return candidate


def build_cli(source: str) -> str:
    candidate = source
    if 'print("write=OFF by default")' in candidate:
        candidate = candidate.replace('print("write=OFF by default")', 'print("write=ON by default")', 1)
    elif 'print("write=ON by default")' not in candidate:
        raise RuntimeError("CODE_STATUS_WRITE_DEFAULT_ANCHOR_MISSING")

    candidate, ok_code = replace_handler_write_default(
        candidate,
        'message == "/code"',
        'message == "/code-self"',
    )
    if not ok_code:
        raise RuntimeError("CODE_HANDLER_WRITE_DEFAULT_ANCHOR_MISSING")

    candidate, ok_self = replace_handler_write_default(
        candidate,
        'message == "/code-self"',
        'message == "/code-write"',
    )
    if not ok_self:
        raise RuntimeError("CODE_SELF_HANDLER_WRITE_DEFAULT_ANCHOR_MISSING")
    return candidate


def show_plan() -> int:
    if not ENGINE.is_file() or not CLI.is_file():
        print("STOP=CANONICAL_BODY_FILES_MISSING")
        return 2
    engine_text = ENGINE.read_text(encoding="utf-8")
    cli_text = CLI.read_text(encoding="utf-8")
    print("AETHER CREATOR // AUTONOMY CUTOVER PLAN")
    print(f"ENGINE={ENGINE}")
    print(f"ENGINE_SHA256={sha256(ENGINE)}")
    print(f"EXPECTED_ENGINE_SHA256={EXPECTED_ENGINE_SHA256}")
    print(f"ALREADY_PATCHED={'YES' if MARKER in engine_text else 'NO'}")
    print(f"PROMPT_GIT_PROHIBITIONS={'YES' if 'Never git commit' in engine_text or 'Never git push' in engine_text else 'NO'}")
    print(f"CODE_STATUS_WRITE_OFF={'YES' if 'write=OFF by default' in cli_text else 'NO'}")
    print("CREATOR_WRITE_DEFAULT=ON")
    print("PROMPT_POLICY_PROHIBITIONS=REMOVE")
    print("PATH_SCOPE_ENFORCEMENT=KEEP")
    print("STRUCTURED_EXECUTOR_RESULTS=KEEP")
    print("SHELL_EXECUTOR_VALIDATION=KEEP")
    print("CODE_RECEIPTS=KEEP")
    print("ROOT_ARBITRARY_SHELL=NO")
    return 0


def apply() -> int:
    if os.geteuid() != 0:
        print("STOP=ROOT_REQUIRED")
        return 2
    if not ENGINE.is_file() or not CLI.is_file():
        print("STOP=CANONICAL_BODY_FILES_MISSING")
        return 3

    engine_text = ENGINE.read_text(encoding="utf-8")
    cli_text = CLI.read_text(encoding="utf-8")
    current = sha256(ENGINE)

    if MARKER in engine_text:
        print("AETHER_CREATOR_AUTONOMY=ALREADY_PATCHED")
        return 0
    if current != EXPECTED_ENGINE_SHA256:
        print(f"STOP=UNEXPECTED_ENGINE_SHA256:{current}")
        return 4

    try:
        engine_candidate = build_engine(engine_text)
        cli_candidate = build_cli(cli_text)
    except RuntimeError as exc:
        print(f"STOP={exc}")
        return 5

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = STATE / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    engine_backup = backup_dir / "code_engine.py.before-autonomy"
    cli_backup = backup_dir / "cli.py.before-autonomy"
    shutil.copy2(ENGINE, engine_backup)
    shutil.copy2(CLI, cli_backup)

    engine_tmp = backup_dir / "code_engine.py.candidate"
    cli_tmp = backup_dir / "cli.py.candidate"
    engine_tmp.write_text(engine_candidate, encoding="utf-8")
    cli_tmp.write_text(cli_candidate, encoding="utf-8")

    compile_result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(engine_tmp), str(cli_tmp)],
        cwd=str(BODY),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if compile_result.returncode != 0:
        print("STOP=CANDIDATE_COMPILE_FAILED")
        print(compile_result.stdout.rstrip())
        return 6

    ENGINE.write_text(engine_candidate, encoding="utf-8")
    CLI.write_text(cli_candidate, encoding="utf-8")

    verify = subprocess.run(
        [sys.executable, "-m", "py_compile", str(ENGINE), str(CLI)],
        cwd=str(BODY),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if verify.returncode != 0:
        shutil.copy2(engine_backup, ENGINE)
        shutil.copy2(cli_backup, CLI)
        print("ROLLBACK=LIVE_COMPILE_FAILED")
        print(verify.stdout.rstrip())
        return 7

    final_engine = ENGINE.read_text(encoding="utf-8")
    final_cli = CLI.read_text(encoding="utf-8")
    checks = {
        "AUTONOMY_MARKER": MARKER in final_engine,
        "PROMPT_GIT_PROHIBITIONS_REMOVED": "Never git commit" not in final_engine and "Never git push" not in final_engine,
        "PROMPT_RESET_CHECKOUT_PROHIBITIONS_REMOVED": "Never git reset" not in final_engine and "Never git checkout" not in final_engine,
        "CREATOR_WRITE_DEFAULT_ON": "    allow_write: bool = True,\n" in final_engine,
        "CLI_WRITE_STATUS_ON": 'print("write=ON by default")' in final_cli,
        "STRUCTURED_JSON_PRESERVED": '"response_format": {"type": "json_object"}' in final_engine,
        "EXECUTOR_RESULT_PRESERVED": "EXECUTOR_RESULT_JSON" in final_engine,
        "SCOPE_ENFORCEMENT_PRESERVED": "path outside active CODE scope rejected" in final_engine,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        shutil.copy2(engine_backup, ENGINE)
        shutil.copy2(cli_backup, CLI)
        print("ROLLBACK=VERIFY_FAILED:" + ",".join(failed))
        return 8

    print("AETHER_CREATOR_AUTONOMY=V1")
    print("CREATOR_WRITE_DEFAULT=ON")
    print("PROMPT_GIT_PROHIBITIONS=REMOVED")
    print("PROMPT_RESET_CHECKOUT_PROHIBITIONS=REMOVED")
    print("PROMPT_DELETE_PROHIBITION=REMOVED")
    print("STRUCTURED_JSON=KEPT")
    print("EXECUTOR_RESULT_AUTHORITY=KEPT")
    print("PATH_SCOPE_ENFORCEMENT=KEPT")
    print("SHELL_EXECUTOR_VALIDATION=KEPT")
    print("CODE_RECEIPTS=KEPT")
    print("ROOT_ARBITRARY_SHELL=NO")
    print("CODE_ENGINE_COMPILE=PASS")
    print("CLI_COMPILE=PASS")
    print(f"NEW_ENGINE_SHA256={sha256(ENGINE)}")
    print(f"BACKUP_DIR={backup_dir}")
    return 0


def rollback() -> int:
    if os.geteuid() != 0:
        print("STOP=ROOT_REQUIRED")
        return 2
    backups = sorted(STATE.glob("*/code_engine.py.before-autonomy"), reverse=True)
    if not backups:
        print("STOP=NO_AUTONOMY_BACKUP")
        return 3
    engine_backup = backups[0]
    cli_backup = engine_backup.parent / "cli.py.before-autonomy"
    if not cli_backup.is_file():
        print("STOP=CLI_BACKUP_MISSING")
        return 4
    shutil.copy2(engine_backup, ENGINE)
    shutil.copy2(cli_backup, CLI)
    proc = subprocess.run([sys.executable, "-m", "py_compile", str(ENGINE), str(CLI)], cwd=str(BODY), check=False)
    if proc.returncode != 0:
        print("STOP=ROLLBACK_COMPILE_FAILED")
        return 5
    print(f"ROLLBACK=PASS:{engine_backup.parent}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--apply", action="store_true")
    g.add_argument("--rollback", action="store_true")
    args = ap.parse_args()
    if args.apply:
        return apply()
    if args.rollback:
        return rollback()
    return show_plan()


if __name__ == "__main__":
    raise SystemExit(main())
