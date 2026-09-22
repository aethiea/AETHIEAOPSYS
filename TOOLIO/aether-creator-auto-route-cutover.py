#!/usr/bin/env python3
"""Route explicit implementation requests into AETHER's native creator lane.

This patch addresses two correctness problems without changing AETHER OPEN style,
llama.cpp middleware, model checkpoint, executor capabilities, path scopes, or
receipts:

1. Plain OPEN implementation requests such as "build ... with code" were being
   answered by the conversational lane instead of body.code_engine.
2. The creator protocol did not explicitly treat TODO/placeholders/stubs as
   unfinished implementation work.

The CLI auto-route is intentionally narrow: it requires an implementation verb
plus a programming/artifact signal. Existing /code* commands remain unchanged.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path("/opt/AETHIEAOPSYS")
BODY = ROOT / "WORKSPACE/codex/aether-chat-aevps"
ENGINE = BODY / "body/code_engine.py"
CLI = BODY / "body/cli.py"
STATE = ROOT / "STATE/aetherbot/creator-routing"

EXPECTED_ENGINE_SHA256 = "c31f6096f0afc489e5b4cf40d434b0636ee1c6e9d04e7ac50e3ebd03ed8d1a33"
ROUTE_MARKER = "# AETHER_CREATOR_AUTO_ROUTE_V1"
TRUTH_MARKER = "# AETHER_CREATOR_COMPLETION_TRUTH_V1"
LOCAL_PROTOCOL_MARKER = "# AETHER_CREATOR_LOCAL_PROTOCOL_V2"
OLD_MODEL_LABEL = 'MODEL = "Mistral-7B-Instruct-v0.3-abliterated-Q4_K_M"'
NEW_MODEL_LABEL = 'MODEL = "mistral_7b_uncensored.Q4_K_M"'

TRUTH_ANCHOR = (
    "EXECUTOR_RESULT_JSON is the runtime result for the preceding action.\n"
    "Use those runtime results as execution state and continue until the operator's task is complete.\n"
)
TRUTH_REPLACEMENT = (
    "EXECUTOR_RESULT_JSON is the runtime result for the preceding action.\n"
    "Use those runtime results as execution state and continue until the operator's task is complete.\n\n"
    "For implementation tasks, TODOs, placeholder comments, pass stubs, NotImplementedError, "
    "omitted implementation, and phrases such as 'add your code here' are unfinished work.\n"
    "Continue using executor results until the requested implementation is complete. "
    "The final action must describe the actual execution state and identify any remaining incomplete part.\n"
)

HELPER = '''# AETHER_CREATOR_AUTO_ROUTE_V1\ndef _looks_like_creator_request(message: str) -> bool:\n    text = " ".join(message.strip().lower().split())\n    if not text or text.startswith("/"):\n        return False\n\n    implementation_verbs = (\n        "build ", "create ", "make ", "implement ", "write ", "code ",\n        "program ", "develop ", "patch ", "debug ", "refactor ", "fix ",\n    )\n    programming_signals = (\n        " with code", " code", "script", "program", "python", "bash",\n        "powershell", "javascript", "typescript", "rust", "golang", " c++",\n        " api", " cli", " bot", "automation", "module", "function", "class",\n        "service", "daemon", "package", ".py", ".sh", ".js", ".ts",\n    )\n    return text.startswith(implementation_verbs) and any(\n        signal in text for signal in programming_signals\n    )\n\n\n'''


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def active_uncensored_model() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:3926/v1/models", timeout=10) as response:
            text = response.read().decode("utf-8", errors="replace")
    except Exception:
        return False
    return "mistral_7b_uncensored.Q4_K_M.gguf" in text


def top_level_main_line(source: str) -> int:
    tree = ast.parse(source)
    matches = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "main"]
    if len(matches) != 1:
        raise RuntimeError(f"TOP_LEVEL_MAIN_COUNT:{len(matches)}")
    return matches[0].lineno


def build_engine(source: str) -> str:
    if TRUTH_MARKER in source:
        candidate = source
    else:
        if LOCAL_PROTOCOL_MARKER not in source:
            raise RuntimeError("LOCAL_CREATOR_PROTOCOL_MARKER_MISSING")
        if source.count(TRUTH_ANCHOR) != 1:
            raise RuntimeError(f"CREATOR_TRUTH_ANCHOR_COUNT:{source.count(TRUTH_ANCHOR)}")
        candidate = source.replace(
            TRUTH_ANCHOR,
            TRUTH_ANCHOR + TRUTH_MARKER + "\n" + TRUTH_REPLACEMENT[len(TRUTH_ANCHOR):],
            1,
        )

    if OLD_MODEL_LABEL in candidate:
        candidate = candidate.replace(OLD_MODEL_LABEL, NEW_MODEL_LABEL, 1)
    elif NEW_MODEL_LABEL not in candidate:
        raise RuntimeError("CREATOR_MODEL_LABEL_ANCHOR_MISSING")
    return candidate


def build_cli(source: str) -> str:
    if ROUTE_MARKER in source:
        return source

    required = ("run_code_task", 'print("write=ON by default")', "/code-write", "/code-self-write")
    missing = [item for item in required if item not in source]
    if missing:
        raise RuntimeError("CLI_CREATOR_MARKERS_MISSING:" + ",".join(missing))

    main_line = top_level_main_line(source)
    lines = source.splitlines(keepends=True)
    insert_at = main_line - 1
    lines.insert(insert_at, HELPER)
    candidate = "".join(lines)

    route_lines = [
        i for i, line in enumerate(candidate.splitlines(keepends=True))
        if 'message == "/code"' in line
    ]
    if len(route_lines) != 1:
        raise RuntimeError(f"CODE_HANDLER_ANCHOR_COUNT:{len(route_lines)}")

    lines = candidate.splitlines(keepends=True)
    idx = route_lines[0]
    stripped = lines[idx].lstrip()
    if not stripped.startswith("if "):
        raise RuntimeError("CODE_HANDLER_IS_NOT_STANDALONE_IF")
    indent = lines[idx][: len(lines[idx]) - len(stripped)]
    block = (
        f'{indent}if _looks_like_creator_request(message):\n'
        f'{indent}    print("CODE ROUTE → AUTO")\n'
        f'{indent}    rc = run_code_task(message, scope="aevps", allow_write=True)\n'
        f'{indent}    print(f"CODE_RETURN={{rc}}")\n'
        f'{indent}    continue\n\n'
    )
    lines.insert(idx, block)
    return "".join(lines)


def compile_pair(engine_path: Path, cli_path: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "py_compile", str(engine_path), str(cli_path)],
        cwd=str(BODY),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return proc.returncode == 0, proc.stdout.rstrip()


def route_probe() -> bool:
    def looks(message: str) -> bool:
        text = " ".join(message.strip().lower().split())
        if not text or text.startswith("/"):
            return False
        verbs = ("build ", "create ", "make ", "implement ", "write ", "code ", "program ", "develop ", "patch ", "debug ", "refactor ", "fix ")
        signals = (" with code", " code", "script", "program", "python", "bash", "powershell", "javascript", "typescript", "rust", "golang", " c++", " api", " cli", " bot", "automation", "module", "function", "class", "service", "daemon", "package", ".py", ".sh", ".js", ".ts")
        return text.startswith(verbs) and any(s in text for s in signals)

    positives = (
        "build a log parser in python",
        "make an API client with code",
        "fix this python script",
        "patch the CLI module",
    )
    negatives = (
        "explain what python is",
        "what is an api",
        "tell me about automation",
        "/code build a parser",
    )
    return all(looks(x) for x in positives) and all(not looks(x) for x in negatives)


def show_plan() -> int:
    if not ENGINE.is_file() or not CLI.is_file():
        print("STOP=CANONICAL_CREATOR_FILES_MISSING")
        return 2
    engine = ENGINE.read_text(encoding="utf-8")
    cli = CLI.read_text(encoding="utf-8")
    print("AETHER CREATOR // AUTO ROUTE + COMPLETION TRUTH PLAN")
    print(f"ENGINE={ENGINE}")
    print(f"ENGINE_SHA256={sha256(ENGINE)}")
    print(f"EXPECTED_ENGINE_SHA256={EXPECTED_ENGINE_SHA256}")
    print(f"CLI={CLI}")
    print(f"CLI_SHA256={sha256(CLI)}")
    print(f"AUTO_ROUTE_PRESENT={'YES' if ROUTE_MARKER in cli else 'NO'}")
    print(f"COMPLETION_TRUTH_PRESENT={'YES' if TRUTH_MARKER in engine else 'NO'}")
    print(f"UNCENSORED_MODEL_3926={'YES' if active_uncensored_model() else 'NO'}")
    print(f"ROUTE_PROBE={'PASS' if route_probe() else 'FAIL'}")
    print("PLAIN_IMPLEMENTATION_REQUEST=CREATOR_ROUTE")
    print("ORDINARY_OPEN_CONVERSATION=UNCHANGED")
    print("EXPLICIT_CODE_COMMANDS=UNCHANGED")
    print("PLACEHOLDER_COMPLETION=UNFINISHED")
    print("OPEN_PROMPT_CHANGED=NO")
    print("MIDDLEWARE_CHANGED=NO")
    print("MODEL_CHECKPOINT_CHANGED=NO")
    print("EXECUTOR_CAPABILITIES_CHANGED=NO")
    print("PATH_SCOPE_CHANGED=NO")
    print("RECEIPTS_CHANGED=NO")
    return 0


def apply() -> int:
    if os.geteuid() != 0:
        print("STOP=ROOT_REQUIRED")
        return 2
    if not ENGINE.is_file() or not CLI.is_file():
        print("STOP=CANONICAL_CREATOR_FILES_MISSING")
        return 3

    engine_source = ENGINE.read_text(encoding="utf-8")
    cli_source = CLI.read_text(encoding="utf-8")
    engine_hash = sha256(ENGINE)

    already = TRUTH_MARKER in engine_source and ROUTE_MARKER in cli_source
    if already:
        print("AETHER_CREATOR_AUTO_ROUTE=ALREADY_PRESENT")
        print(f"ENGINE_SHA256={engine_hash}")
        print(f"CLI_SHA256={sha256(CLI)}")
        return 0

    if engine_hash != EXPECTED_ENGINE_SHA256:
        print("STOP=UNEXPECTED_ENGINE_SHA256")
        print(f"EXPECTED={EXPECTED_ENGINE_SHA256}")
        print(f"ACTUAL={engine_hash}")
        return 4
    if not active_uncensored_model():
        print("STOP=UNCENSORED_MODEL_NOT_LIVE_ON_3926")
        return 5
    if not route_probe():
        print("STOP=ROUTE_PROBE_FAILED")
        return 6

    try:
        engine_candidate = build_engine(engine_source)
        cli_candidate = build_cli(cli_source)
        ast.parse(engine_candidate)
        ast.parse(cli_candidate)
    except (RuntimeError, SyntaxError) as exc:
        print(f"STOP=CANDIDATE_BUILD:{exc}")
        return 7

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    backup_dir = STATE / stamp
    backup_dir.mkdir(parents=True, exist_ok=False)
    engine_backup = backup_dir / "code_engine.py.before"
    cli_backup = backup_dir / "cli.py.before"
    shutil.copy2(ENGINE, engine_backup)
    shutil.copy2(CLI, cli_backup)

    engine_tmp = backup_dir / "code_engine.py.candidate"
    cli_tmp = backup_dir / "cli.py.candidate"
    engine_tmp.write_text(engine_candidate, encoding="utf-8")
    cli_tmp.write_text(cli_candidate, encoding="utf-8")
    ok, output = compile_pair(engine_tmp, cli_tmp)
    if not ok:
        print("STOP=CANDIDATE_COMPILE_FAILED")
        print(output)
        return 8

    ENGINE.write_text(engine_candidate, encoding="utf-8")
    CLI.write_text(cli_candidate, encoding="utf-8")
    ok, output = compile_pair(ENGINE, CLI)
    if not ok:
        shutil.copy2(engine_backup, ENGINE)
        shutil.copy2(cli_backup, CLI)
        print("ROLLBACK=LIVE_COMPILE_FAILED")
        print(output)
        return 9

    final_engine = ENGINE.read_text(encoding="utf-8")
    final_cli = CLI.read_text(encoding="utf-8")
    checks = {
        "AUTO_ROUTE": ROUTE_MARKER in final_cli,
        "COMPLETION_TRUTH": TRUTH_MARKER in final_engine,
        "STRUCTURED_JSON": '"response_format": {"type": "json_object"}' in final_engine,
        "EXECUTOR_RESULTS": "EXECUTOR_RESULT_JSON" in final_engine,
        "WRITE_DEFAULT": "    allow_write: bool = True," in final_engine,
        "RECEIPTS": "CODE_RECEIPTS" in final_engine,
        "PATH_SCOPE": "path outside active CODE scope rejected" in final_engine,
        "MODEL_LABEL": NEW_MODEL_LABEL in final_engine,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        shutil.copy2(engine_backup, ENGINE)
        shutil.copy2(cli_backup, CLI)
        print("ROLLBACK=VERIFY_FAILED:" + ",".join(failed))
        return 10

    print("AETHER_CREATOR_AUTO_ROUTE=V1")
    print("PLAIN_IMPLEMENTATION_REQUEST=CREATOR_ROUTE")
    print("COMPLETION_TRUTH=V1")
    print("PLACEHOLDER_COMPLETION=UNFINISHED")
    print("CREATOR_MODEL_LABEL=mistral_7b_uncensored.Q4_K_M")
    print("STRUCTURED_JSON=KEPT")
    print("EXECUTOR_RESULTS=KEPT")
    print("CREATOR_WRITE_DEFAULT=ON")
    print("PATH_SCOPE=KEPT")
    print("CODE_RECEIPTS=KEPT")
    print("OPEN_PROMPT_CHANGED=NO")
    print("MIDDLEWARE_CHANGED=NO")
    print("MODEL_CHECKPOINT_CHANGED=NO")
    print("EXECUTOR_CAPABILITIES_CHANGED=NO")
    print("CODE_ENGINE_COMPILE=PASS")
    print("CLI_COMPILE=PASS")
    print(f"ENGINE_SHA256_NEW={sha256(ENGINE)}")
    print(f"CLI_SHA256_NEW={sha256(CLI)}")
    print(f"BACKUP_DIR={backup_dir}")
    return 0


def rollback() -> int:
    if os.geteuid() != 0:
        print("STOP=ROOT_REQUIRED")
        return 2
    backups = sorted(STATE.glob("*/code_engine.py.before"), reverse=True)
    if not backups:
        print("STOP=NO_ROUTING_BACKUP")
        return 3
    engine_backup = backups[0]
    cli_backup = engine_backup.parent / "cli.py.before"
    if not cli_backup.is_file():
        print("STOP=CLI_BACKUP_MISSING")
        return 4
    shutil.copy2(engine_backup, ENGINE)
    shutil.copy2(cli_backup, CLI)
    ok, output = compile_pair(ENGINE, CLI)
    if not ok:
        print("STOP=ROLLBACK_COMPILE_FAILED")
        print(output)
        return 5
    print(f"ROLLBACK=PASS:{engine_backup.parent}")
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
