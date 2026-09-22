#!/usr/bin/env python3
"""Expand AETHER creator auto-route intent detection for inspection/reuse requests.

Targets the live CLI produced by AETHER_CREATOR_AUTO_ROUTE_V4. This patch only
updates the routing helper so requests beginning with inspection/reuse verbs can
reach the native creator lane. It does not change the model, middleware, creator
executor, path scopes, receipts, or OPEN prompt.
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
BODY = ROOT / "WORKSPACE/codex/aether-chat-aevps"
CLI = BODY / "body/cli.py"
STATE = ROOT / "STATE/aetherbot/creator-route-intent"

EXPECTED_CLI_SHA256 = "470110de7e5f4b91d7f2ced9393bdeb34b87b21a5a35e72274c7e4b9b4ed345d"
V4_MARKER = "# AETHER_CREATOR_AUTO_ROUTE_V4"
V5_MARKER = "# AETHER_CREATOR_ROUTE_INTENT_V5"

OLD_VERBS = '''    verbs = (\n        "build ", "create ", "make ", "implement ", "write ", "code ",\n        "program ", "develop ", "patch ", "debug ", "refactor ", "fix ",\n        "wire ", "connect ", "integrate ", "extend ", "update ",\n        "repair ", "modify ",\n    )\n'''

NEW_VERBS = '''    # AETHER_CREATOR_ROUTE_INTENT_V5\n    verbs = (\n        "build ", "create ", "make ", "implement ", "write ", "code ",\n        "program ", "develop ", "patch ", "debug ", "refactor ", "fix ",\n        "wire ", "connect ", "integrate ", "extend ", "update ",\n        "repair ", "modify ",\n        "inspect ", "review ", "audit ", "discover ", "find ", "locate ",\n        "reuse ", "examine ", "check ", "trace ", "map ",\n        "look at ", "look through ",\n    )\n'''

OLD_SIGNALS = '''    signals = (\n        " with code", " code", "script", "program", "python", "bash",\n        "powershell", "javascript", "typescript", "rust", "golang", " c++",\n        " api", " cli", " bot", "automation", "module", "function", "class",\n        "service", "daemon", "package", "repo", "repository",\n        "aether", "aevps", "aethiea", ".py", ".sh", ".js", ".ts",\n    )\n'''

NEW_SIGNALS = '''    signals = (\n        " with code", " code", "script", "program", "python", "bash",\n        "powershell", "javascript", "typescript", "rust", "golang", " c++",\n        " api", " cli", " bot", "automation", "module", "function", "class",\n        "service", "daemon", "package", "repo", "repository",\n        "aether", "aevps", "aethiea", "creator", "implementation",\n        "codebase", "component", "existing", "already built", "we built",\n        "what we built", "prior work", "receipts",\n        ".py", ".sh", ".js", ".ts",\n    )\n'''


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def candidate(source: str) -> str:
    if V5_MARKER in source:
        return source
    if V4_MARKER not in source:
        raise RuntimeError("V4_ROUTE_MARKER_MISSING")
    if source.count(OLD_VERBS) != 1:
        raise RuntimeError(f"V4_VERB_BLOCK_COUNT:{source.count(OLD_VERBS)}")
    if source.count(OLD_SIGNALS) != 1:
        raise RuntimeError(f"V4_SIGNAL_BLOCK_COUNT:{source.count(OLD_SIGNALS)}")
    out = source.replace(OLD_VERBS, NEW_VERBS, 1)
    out = out.replace(OLD_SIGNALS, NEW_SIGNALS, 1)
    return out


def compile_file(path: Path) -> tuple[bool, str]:
    p = subprocess.run(
        [sys.executable, "-m", "py_compile", str(path)],
        cwd=str(BODY),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return p.returncode == 0, p.stdout.rstrip()


def probe_text() -> None:
    def looks(message: str) -> bool:
        text = " ".join(message.strip().lower().split())
        if not text or text.startswith("/"):
            return False
        verbs = (
            "build ", "create ", "make ", "implement ", "write ", "code ",
            "program ", "develop ", "patch ", "debug ", "refactor ", "fix ",
            "wire ", "connect ", "integrate ", "extend ", "update ",
            "repair ", "modify ", "inspect ", "review ", "audit ",
            "discover ", "find ", "locate ", "reuse ", "examine ",
            "check ", "trace ", "map ", "look at ", "look through ",
        )
        signals = (
            " with code", " code", "script", "program", "python", "bash",
            "powershell", "javascript", "typescript", "rust", "golang", " c++",
            " api", " cli", " bot", "automation", "module", "function", "class",
            "service", "daemon", "package", "repo", "repository", "aether",
            "aevps", "aethiea", "creator", "implementation", "codebase",
            "component", "existing", "already built", "we built", "what we built",
            "prior work", "receipts", ".py", ".sh", ".js", ".ts",
        )
        return text.startswith(verbs) and any(s in text for s in signals)

    tests = {
        "inspect_existing_creator": looks("Inspect the existing AETHIEA/AETHER creator implementation first."),
        "look_at_existing": looks("look at what we already built in AETHER"),
        "reuse_creator": looks("reuse the existing creator implementation"),
        "ordinary_question_stays_open": not looks("what is an api"),
        "slash_command_stays_explicit": not looks("/code inspect existing creator"),
    }
    for name, ok in tests.items():
        print(f"PROBE_{name.upper()}={'PASS' if ok else 'FAIL'}")
    if not all(tests.values()):
        raise RuntimeError("ROUTE_INTENT_PROBE_FAILED")


def show_plan() -> int:
    if not CLI.is_file():
        print("STOP=CLI_MISSING")
        return 2
    print("AETHER CREATOR // ROUTE INTENT V5 PLAN")
    print(f"CLI_SHA256={sha256(CLI)}")
    print(f"EXPECTED_CLI_SHA256={EXPECTED_CLI_SHA256}")
    print(f"V4_PRESENT={'YES' if V4_MARKER in CLI.read_text(encoding='utf-8') else 'NO'}")
    print(f"V5_PRESENT={'YES' if V5_MARKER in CLI.read_text(encoding='utf-8') else 'NO'}")
    probe_text()
    print("INSPECTION_REUSE_REQUESTS=CREATOR_ROUTE")
    print("OPEN_PROMPT_CHANGED=NO")
    print("CREATOR_ENGINE_CHANGED=NO")
    print("MODEL_CHANGED=NO")
    print("MIDDLEWARE_CHANGED=NO")
    print("EXECUTOR_CHANGED=NO")
    print("PATH_SCOPE_CHANGED=NO")
    print("RECEIPTS_CHANGED=NO")
    return 0


def apply() -> int:
    if os.geteuid() != 0:
        print("STOP=ROOT_REQUIRED")
        return 2
    if not CLI.is_file():
        print("STOP=CLI_MISSING")
        return 3

    source = CLI.read_text(encoding="utf-8")
    if V5_MARKER in source:
        print("AETHER_CREATOR_ROUTE_INTENT=ALREADY_V5")
        print(f"CLI_SHA256={sha256(CLI)}")
        return 0

    actual = sha256(CLI)
    if actual != EXPECTED_CLI_SHA256:
        print("STOP=UNEXPECTED_CLI_SHA256")
        print(f"EXPECTED={EXPECTED_CLI_SHA256}")
        print(f"ACTUAL={actual}")
        return 4

    try:
        probe_text()
        out = candidate(source)
        compile(out, str(CLI), "exec")
    except Exception as exc:
        print(f"STOP=CANDIDATE_BUILD:{exc}")
        return 5

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    backup_dir = STATE / stamp
    backup_dir.mkdir(parents=True, exist_ok=False)
    backup = backup_dir / "cli.py.before"
    temp = backup_dir / "cli.py.candidate"
    shutil.copy2(CLI, backup)
    temp.write_text(out, encoding="utf-8")

    ok, msg = compile_file(temp)
    if not ok:
        print("STOP=CANDIDATE_COMPILE_FAILED")
        print(msg)
        return 6

    CLI.write_text(out, encoding="utf-8")
    ok, msg = compile_file(CLI)
    if not ok:
        shutil.copy2(backup, CLI)
        print("ROLLBACK=LIVE_COMPILE_FAILED")
        print(msg)
        return 7

    final = CLI.read_text(encoding="utf-8")
    if V5_MARKER not in final or V4_MARKER not in final:
        shutil.copy2(backup, CLI)
        print("ROLLBACK=MARKER_VERIFY_FAILED")
        return 8

    print("AETHER_CREATOR_ROUTE_INTENT=V5")
    print("INSPECT_REVIEW_AUDIT_DISCOVER_REUSE=CREATOR_ROUTE")
    print("EXISTING_ALREADY_BUILT_SIGNALS=RECOGNIZED")
    print("V4_AUTO_ROUTE=KEPT")
    print("REUSE_FIRST_ENGINE=UNCHANGED")
    print("OPEN_PROMPT_CHANGED=NO")
    print("MODEL_CHANGED=NO")
    print("MIDDLEWARE_CHANGED=NO")
    print("EXECUTOR_CHANGED=NO")
    print("PATH_SCOPE_CHANGED=NO")
    print("RECEIPTS_CHANGED=NO")
    print("CLI_COMPILE=PASS")
    print(f"CLI_SHA256_NEW={sha256(CLI)}")
    print(f"BACKUP_DIR={backup_dir}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    return apply() if args.apply else show_plan()


if __name__ == "__main__":
    raise SystemExit(main())
