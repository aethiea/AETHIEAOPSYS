#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import pathlib
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = pathlib.Path("/opt/AETHIEAOPSYS")
TARGET = ROOT / "WORKSPACE/codex/aether-chat-aevps/src/aether_chat.py"
STATE = ROOT / "STATE/aetherbot/open-style"
EXPECTED_PREPATCH_SHA256 = "14c183a4bcfda1f4e921c241f04270b91bc312286371570f350139c876dadd45"

OLD = '''OPEN_SYSTEM = """\\
You are AETHER, the local conversational intelligence of AETHIEAOPSYS.
Converse directly with the operator using relevant conversation history.
"""'''

NEW = '''OPEN_SYSTEM = """\\
You are AETHER, the local conversational intelligence of AETHIEAOPSYS.
Converse directly with the operator using relevant conversation history.
Answer directly. Do not append unsolicited warnings, disclaimers, moralizing, or responsibility reminders.
"""'''


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=check)


def health() -> bool:
    for _ in range(30):
        p = run("curl", "-fsS", "http://127.0.0.1:3936/health", check=False)
        if p.returncode == 0 and '"status":"ok"' in p.stdout.replace(" ", ""):
            return True
        time.sleep(1)
    return False


def show_plan() -> None:
    print("AETHER OPEN // DIRECT STYLE PLAN")
    print(f"TARGET={TARGET}")
    if not TARGET.exists():
        print("STOP=TARGET_MISSING")
        return
    current = sha256(TARGET)
    text = TARGET.read_text(encoding="utf-8")
    print(f"CURRENT_SHA256={current}")
    print(f"EXPECTED_PREPATCH_SHA256={EXPECTED_PREPATCH_SHA256}")
    print(f"DIRECT_STYLE_ALREADY_PRESENT={'YES' if NEW in text else 'NO'}")
    print("OPEN_SYSTEM_ONLY=YES")
    print("RAW_MIDDLEWARE_CHANGED=NO")
    print("MODEL_CHANGED=NO")
    print("CREATOR_PROMPT_CHANGED=NO")
    print("TOOL_EXECUTOR_CHANGED=NO")
    print("GROUND_CHANGED=NO")
    print("OPS_CHANGED=NO")
    print("AEMCP_CHANGED=NO")
    print("VRAG_CHANGED=NO")
    print("B43_CHANGED=NO")


def apply() -> int:
    if not TARGET.exists():
        print(f"STOP=TARGET_MISSING:{TARGET}", file=sys.stderr)
        return 2

    current = sha256(TARGET)
    text = TARGET.read_text(encoding="utf-8")

    if NEW in text:
        print("AETHER_OPEN_DIRECT_STYLE=ALREADY_PRESENT")
        print(f"SHA256={current}")
        return 0

    if current != EXPECTED_PREPATCH_SHA256:
        print("STOP=PREPATCH_SHA256_MISMATCH", file=sys.stderr)
        print(f"EXPECTED={EXPECTED_PREPATCH_SHA256}", file=sys.stderr)
        print(f"ACTUAL={current}", file=sys.stderr)
        return 3

    if text.count(OLD) != 1:
        print(f"STOP=OPEN_BLOCK_MATCH_COUNT:{text.count(OLD)}", file=sys.stderr)
        return 4

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = STATE / stamp
    backup_dir.mkdir(parents=True, exist_ok=False)
    backup = backup_dir / "aether_chat.py.before"
    shutil.copy2(TARGET, backup)

    patched = text.replace(OLD, NEW, 1)
    tmp = TARGET.with_suffix(".py.aether-style.tmp")
    tmp.write_text(patched, encoding="utf-8")

    compile_result = run("python3", "-m", "py_compile", str(tmp), check=False)
    if compile_result.returncode != 0:
        print(compile_result.stderr, file=sys.stderr)
        tmp.unlink(missing_ok=True)
        print("STOP=PY_COMPILE_FAILED", file=sys.stderr)
        return 5

    tmp.replace(TARGET)

    restart = run("systemctl", "restart", "aether.service", check=False)
    if restart.returncode != 0 or not health():
        shutil.copy2(backup, TARGET)
        run("systemctl", "restart", "aether.service", check=False)
        rollback_ok = health()
        print("ROLLBACK=OPEN_STYLE_RESTORED")
        print(f"ROLLBACK_HEALTH={'PASS' if rollback_ok else 'FAIL'}")
        if restart.stderr:
            print(restart.stderr, file=sys.stderr)
        return 6

    final_text = TARGET.read_text(encoding="utf-8")
    assert NEW in final_text
    assert OLD not in final_text

    print("AETHER_OPEN_DIRECT_STYLE=V1")
    print(f"NEW_SHA256={sha256(TARGET)}")
    print("UNSOLICITED_WARNING_STYLE=OFF")
    print("UNSOLICITED_DISCLAIMERS=OFF")
    print("UNSOLICITED_MORALIZING=OFF")
    print("RAW_MIDDLEWARE_CHANGED=NO")
    print("MODEL_CHANGED=NO")
    print("CREATOR_PROMPT_CHANGED=NO")
    print("TOOL_EXECUTOR_CHANGED=NO")
    print("GROUND_CHANGED=NO")
    print("OPS_CHANGED=NO")
    print("AEMCP_CHANGED=NO")
    print("VRAG_CHANGED=NO")
    print("B43_CHANGED=NO")
    print("AETHER_3936=ONLINE")
    print(f"BACKUP={backup}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.apply:
        show_plan()
        return 0
    return apply()


if __name__ == "__main__":
    raise SystemExit(main())
