#!/usr/bin/env python3
"""Reconnect canonical AETHER code_engine to the live llama.cpp middleware.

This changes only body/code_engine.py. It preserves the existing canonical
AETHER body, CLI code hooks, scopes, receipts, read/search/write actions, and
bounded executor. The creator identity remains AETHER; AEVPS performs the
structured actions AETHER emits.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path("/opt/AETHIEAOPSYS")
BODY = ROOT / "WORKSPACE/codex/aether-chat-aevps"
TARGET = BODY / "body/code_engine.py"
CLI = BODY / "body/cli.py"
STATE = ROOT / "STATE/aetherbot/creator-engine"
MARKER = "# AETHER_CREATOR_LLAMA_CPP_V1"
OLD_URL = 'OLLAMA_URL = "http://127.0.0.1:11434/api/chat"'
OLD_MODEL = 'MODEL = "qwen2.5-coder:3b"'
NEW_URL = 'LLAMA_URL = "http://127.0.0.1:3926/v1/chat/completions"'
NEW_MODEL = 'MODEL = "Mistral-7B-Instruct-v0.3-abliterated-Q4_K_M"'

OLD_FUNCTION = '''def ollama(messages: list[dict]) -> str:\n    payload = json.dumps(\n        {\n            "model": MODEL,\n            "messages": messages,\n            "stream": False,\n            "options": {\n                "temperature": 0.1,\n            },\n        }\n    ).encode()\n\n    request = urllib.request.Request(\n        OLLAMA_URL,\n        data=payload,\n        headers={"Content-Type": "application/json"},\n        method="POST",\n    )\n\n    with urllib.request.urlopen(\n        request,\n        timeout=300,\n    ) as response:\n        data = json.load(response)\n\n    return data["message"]["content"].strip()\n'''

NEW_FUNCTION = '''def ollama(messages: list[dict]) -> str:\n    # Historical function name retained to avoid changing the existing\n    # creator loop. The backend is now llama.cpp's OpenAI-compatible API.\n    payload = json.dumps(\n        {\n            "model": "local",\n            "messages": messages,\n            "stream": False,\n            "temperature": 0.1,\n            "max_tokens": 1800,\n        }\n    ).encode()\n\n    request = urllib.request.Request(\n        LLAMA_URL,\n        data=payload,\n        headers={\n            "Content-Type": "application/json",\n            "Accept": "application/json",\n        },\n        method="POST",\n    )\n\n    with urllib.request.urlopen(\n        request,\n        timeout=480,\n    ) as response:\n        data = json.load(response)\n\n    return data["choices"][0]["message"]["content"].strip()\n'''


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def cli_hook_ok(text: str) -> bool:
    return (
        "run_code_task" in text
        and "/code-write" in text
        and "/code-self-write" in text
    )


def llama_model_ok() -> bool:
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:3926/v1/models", timeout=10
        ) as response:
            text = response.read().decode("utf-8", errors="replace")
    except Exception:
        return False
    return "Mistral-7B-Instruct-v0.3-abliterated-Q4_K_M.gguf" in text


def build_candidate(source: str) -> str:
    if MARKER in source:
        return source

    required = [OLD_URL, OLD_MODEL, OLD_FUNCTION]
    missing = [item[:80] for item in required if item not in source]
    if missing:
        raise RuntimeError("STALE_BACKEND_MARKERS_NOT_FOUND")

    candidate = source.replace(OLD_URL, NEW_URL, 1)
    candidate = candidate.replace(OLD_MODEL, NEW_MODEL, 1)
    candidate = candidate.replace(OLD_FUNCTION, NEW_FUNCTION, 1)

    old_identity = "You are the local coding engine for AETHERBOT."
    new_identity = (
        "You are AETHER operating your native AEVPS creator/programming capability."
    )
    if old_identity in candidate:
        candidate = candidate.replace(old_identity, new_identity, 1)

    old_scope = "AETHERBOT will provide an ACTIVE CODE SCOPE for each task."
    new_scope = "The active AETHER session provides an ACTIVE CODE SCOPE for each task."
    if old_scope in candidate:
        candidate = candidate.replace(old_scope, new_scope, 1)

    anchor = "AEVPS_ROOT = Path(\"/opt/AETHIEAOPSYS\").resolve()"
    if anchor not in candidate:
        raise RuntimeError("AEVPS_ROOT_ANCHOR_NOT_FOUND")
    candidate = candidate.replace(anchor, MARKER + "\n" + anchor, 1)
    return candidate


def show_plan() -> int:
    if not TARGET.is_file() or not CLI.is_file():
        print("STOP=CANONICAL_BODY_FILES_MISSING")
        return 2
    source = TARGET.read_text(encoding="utf-8")
    cli = CLI.read_text(encoding="utf-8", errors="replace")
    print("AETHER CREATOR // LLAMA.CPP CUTOVER PLAN")
    print(f"TARGET={TARGET}")
    print(f"CURRENT_SHA256={sha256(TARGET)}")
    print(f"ALREADY_PATCHED={'YES' if MARKER in source else 'NO'}")
    print(f"STALE_OLLAMA_BACKEND={'YES' if OLD_URL in source else 'NO'}")
    print(f"STALE_QWEN_CODE_MODEL={'YES' if OLD_MODEL in source else 'NO'}")
    print(f"CLI_CREATOR_HOOK={'PASS' if cli_hook_ok(cli) else 'MISSING'}")
    print("CREATOR_IDENTITY=AETHER")
    print("INFERENCE_BACKEND=127.0.0.1:3926/v1/chat/completions")
    print("AEVPS_SCOPE_CHANGED=NO")
    print("CODE_RECEIPTS_CHANGED=NO")
    print("TOOL_IMPLEMENTATION_CHANGED=NO")
    print("AETHER_OPEN_CHAT_CHANGED=NO")
    print("MIDDLEWARE_MODEL_CHANGED=NO")
    return 0


def apply() -> int:
    if os.geteuid() != 0:
        print("STOP=ROOT_REQUIRED")
        return 2
    if not TARGET.is_file() or not CLI.is_file():
        print("STOP=CANONICAL_BODY_FILES_MISSING")
        return 2

    cli = CLI.read_text(encoding="utf-8", errors="replace")
    if not cli_hook_ok(cli):
        print("STOP=CLI_CREATOR_HOOK_MISSING")
        return 3

    source = TARGET.read_text(encoding="utf-8")
    if MARKER in source:
        print("AETHER_CREATOR=ALREADY_LLAMA_CPP")
        print(f"CURRENT_SHA256={sha256(TARGET)}")
        print(f"LLAMA_MODEL_PROBE={'PASS' if llama_model_ok() else 'FAIL'}")
        return 0

    try:
        candidate = build_candidate(source)
    except RuntimeError as exc:
        print(f"STOP={exc}")
        print(f"CURRENT_SHA256={sha256(TARGET)}")
        return 4

    if not llama_model_ok():
        print("STOP=ABLITERATED_LLAMA_MODEL_NOT_LIVE_ON_3926")
        return 5

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    backup_dir = STATE / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / "code_engine.py.before"
    shutil.copy2(TARGET, backup)

    candidate_path = backup_dir / "code_engine.py.candidate"
    candidate_path.write_text(candidate, encoding="utf-8")
    compile_result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(candidate_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if compile_result.returncode != 0:
        print("STOP=CANDIDATE_COMPILE_FAILED")
        print(compile_result.stderr.rstrip())
        return 6

    temp = TARGET.with_suffix(".py.creator-new")
    temp.write_text(candidate, encoding="utf-8")
    os.chmod(temp, TARGET.stat().st_mode)
    os.replace(temp, TARGET)

    verify = subprocess.run(
        [sys.executable, "-m", "py_compile", str(TARGET)],
        text=True,
        capture_output=True,
        check=False,
    )
    if verify.returncode != 0:
        shutil.copy2(backup, TARGET)
        print("ROLLBACK=LIVE_COMPILE_FAILED")
        print(verify.stderr.rstrip())
        return 7

    import_probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from body.code_engine import MODEL,LLAMA_URL,get_workspace;"
                "print('MODEL='+MODEL);print('LLAMA_URL='+LLAMA_URL);"
                "print('AEVPS_SCOPE='+str(get_workspace('aevps')));"
                "print('SELF_SCOPE='+str(get_workspace('self')))"
            ),
        ],
        cwd=str(BODY),
        text=True,
        capture_output=True,
        check=False,
    )
    if import_probe.returncode != 0:
        shutil.copy2(backup, TARGET)
        print("ROLLBACK=IMPORT_PROBE_FAILED")
        print(import_probe.stdout.rstrip())
        print(import_probe.stderr.rstrip())
        return 8

    print(import_probe.stdout.rstrip())
    print("AETHER_CREATOR_ENGINE=LLAMA_CPP")
    print("CREATOR_IDENTITY=AETHER")
    print("CLI_CREATOR_HOOK=PASS")
    print("ABLITERATED_MODEL_PROBE=PASS")
    print("CODE_ENGINE_COMPILE=PASS")
    print("AEVPS_SCOPE_CHANGED=NO")
    print("CODE_RECEIPTS_CHANGED=NO")
    print("TOOL_IMPLEMENTATION_CHANGED=NO")
    print("AETHER_OPEN_CHAT_CHANGED=NO")
    print("MIDDLEWARE_MODEL_CHANGED=NO")
    print(f"NEW_SHA256={sha256(TARGET)}")
    print(f"BACKUP={backup}")
    return 0


def rollback() -> int:
    if os.geteuid() != 0:
        print("STOP=ROOT_REQUIRED")
        return 2
    backups = sorted(STATE.glob("*/code_engine.py.before"), reverse=True)
    if not backups:
        print("STOP=NO_BACKUP_FOUND")
        return 3
    backup = backups[0]
    shutil.copy2(backup, TARGET)
    check = subprocess.run(
        [sys.executable, "-m", "py_compile", str(TARGET)], check=False
    )
    if check.returncode != 0:
        print("STOP=ROLLBACK_COMPILE_FAILED")
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
    return show_plan()


if __name__ == "__main__":
    raise SystemExit(main())
