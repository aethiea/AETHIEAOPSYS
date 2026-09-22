#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path('/opt/AETHIEAOPSYS')
BODY = ROOT / 'WORKSPACE/codex/aether-chat-aevps'
TARGET = BODY / 'body/code_engine.py'
STATE = ROOT / 'STATE/aetherbot/creator-discovery-budget'
EXPECTED_SHA256 = 'a1ffa9df0d9365655bfb5c659419d69d236fd889c9342cbf8d90d9c44664c45e'
MARKER = '# AETHER_CREATOR_DISCOVERY_BUDGET_V9'

OLD_SIGNATURE = 'def ollama(messages: list[dict]) -> str:\n'
NEW_SIGNATURE = 'def ollama(messages: list[dict], *, max_tokens: int = 1024) -> str:\n'
OLD_BUDGET = '            "max_tokens": 1024,\n'
NEW_BUDGET = '            "max_tokens": max_tokens,\n'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def verify_step_scope(text: str) -> None:
    tree = ast.parse(text)
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    calls = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == 'ollama'
    ]
    if len(calls) != 1:
        raise RuntimeError(f'OLLAMA_AST_CALL_COUNT={len(calls)}')

    node: ast.AST | None = calls[0]
    found_run = False
    found_step_loop = False
    while node in parents:
        node = parents[node]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == 'run_code_task':
                found_run = True
            break
        if isinstance(node, (ast.For, ast.AsyncFor)):
            target = node.target
            if isinstance(target, ast.Name) and target.id == 'step':
                found_step_loop = True

    if not found_run:
        raise RuntimeError('OLLAMA_CALL_NOT_IN_RUN_CODE_TASK')
    if not found_step_loop:
        raise RuntimeError('OLLAMA_CALL_NOT_IN_STEP_LOOP')


def build_candidate(text: str) -> str:
    if MARKER in text:
        return text

    required = [
        '# AETHER_CREATOR_ACTION_SCHEMA_V8',
        '# AETHER_CREATOR_REUSE_FIRST_V2',
        '# AETHER_CREATOR_COMPLETION_TRUTH_V1',
        '# AETHER_CREATOR_TURN_BUDGET_V7',
        'except TimeoutError:',
        'EXECUTOR_RESULT_JSON',
    ]
    missing = [x for x in required if x not in text]
    if missing:
        raise RuntimeError('REQUIRED_MARKERS_MISSING=' + ','.join(missing))

    if text.count(OLD_SIGNATURE) != 1:
        raise RuntimeError(f'OLLAMA_SIGNATURE_COUNT={text.count(OLD_SIGNATURE)}')
    if text.count(OLD_BUDGET) != 1:
        raise RuntimeError(f'STATIC_BUDGET_COUNT={text.count(OLD_BUDGET)}')

    verify_step_scope(text)

    pattern = re.compile(r'(?m)^(?P<i>[ \t]*)raw = ollama\(messages\)[ \t]*$')
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f'OLLAMA_TEXT_CALL_COUNT={len(matches)}')

    out = text.replace(
        OLD_SIGNATURE,
        MARKER + '\n' + NEW_SIGNATURE,
        1,
    )
    out = out.replace(OLD_BUDGET, NEW_BUDGET, 1)

    m = pattern.search(out)
    if m is None:
        raise RuntimeError('OLLAMA_CALL_LOST_AFTER_SIGNATURE_PATCH')
    indent = m.group('i')
    replacement = (
        f'{indent}raw = ollama(\n'
        f'{indent}    messages,\n'
        f'{indent}    max_tokens=(256 if step == 1 else 1024),\n'
        f'{indent})'
    )
    out = out[:m.start()] + replacement + out[m.end():]

    ast.parse(out)
    return out


def main() -> int:
    if os.geteuid() != 0:
        print('STOP=ROOT_REQUIRED')
        return 2
    if not TARGET.is_file():
        print(f'STOP=TARGET_MISSING:{TARGET}')
        return 3

    current = sha256(TARGET)
    text = TARGET.read_text(encoding='utf-8')

    print('AETHER CREATOR // DISCOVERY BUDGET V9')
    print(f'TARGET={TARGET}')
    print(f'CURRENT_SHA256={current}')
    print(f'EXPECTED_SHA256={EXPECTED_SHA256}')
    print(f'ALREADY_PATCHED={"YES" if MARKER in text else "NO"}')
    print('STEP1_MAX_TOKENS=256')
    print('STEP2_PLUS_MAX_TOKENS=1024')
    print('ACTION_SCHEMA_V8=KEPT')
    print('REUSE_FIRST=KEPT')
    print('HTTP_TIMEOUT=480S_KEPT')
    print('MODEL=UNCHANGED')
    print('MIDDLEWARE=UNCHANGED')
    print('EXECUTOR=UNCHANGED')
    print('PATH_SCOPE=UNCHANGED')
    print('RECEIPTS=UNCHANGED')

    if MARKER in text:
        return 0
    if current != EXPECTED_SHA256:
        print('STOP=UNEXPECTED_ENGINE_SHA256')
        return 4

    try:
        candidate = build_candidate(text)
    except Exception as exc:
        print(f'STOP=CANDIDATE_BUILD:{exc}')
        return 5

    stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    backup_dir = STATE / stamp
    backup_dir.mkdir(parents=True, exist_ok=False)
    backup = backup_dir / 'code_engine.py.before'
    candidate_path = backup_dir / 'code_engine.py.candidate'
    shutil.copy2(TARGET, backup)
    candidate_path.write_text(candidate, encoding='utf-8')

    check = subprocess.run(
        [sys.executable, '-m', 'py_compile', str(candidate_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if check.returncode != 0:
        print('STOP=CANDIDATE_COMPILE_FAILED')
        print(check.stdout.rstrip())
        return 6

    TARGET.write_text(candidate, encoding='utf-8')
    check = subprocess.run(
        [sys.executable, '-m', 'py_compile', str(TARGET)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if check.returncode != 0:
        shutil.copy2(backup, TARGET)
        print('ROLLBACK=LIVE_COMPILE_FAILED')
        print(check.stdout.rstrip())
        return 7

    final = TARGET.read_text(encoding='utf-8')
    required_final = [
        MARKER,
        'max_tokens: int = 1024',
        '"max_tokens": max_tokens,',
        'max_tokens=(256 if step == 1 else 1024)',
        '# AETHER_CREATOR_ACTION_SCHEMA_V8',
        '# AETHER_CREATOR_REUSE_FIRST_V2',
        'except TimeoutError:',
    ]
    missing = [x for x in required_final if x not in final]
    if missing:
        shutil.copy2(backup, TARGET)
        print('ROLLBACK=VERIFY_FAILED:' + ','.join(missing))
        return 8

    print('AETHER_CREATOR_DISCOVERY_BUDGET=V9')
    print('STEP1_MAX_TOKENS=256')
    print('STEP2_PLUS_MAX_TOKENS=1024')
    print('ACTION_SCHEMA_V8=KEPT')
    print('CODE_ENGINE_COMPILE=PASS')
    print(f'ENGINE_SHA256_NEW={sha256(TARGET)}')
    print(f'BACKUP_DIR={backup_dir}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
