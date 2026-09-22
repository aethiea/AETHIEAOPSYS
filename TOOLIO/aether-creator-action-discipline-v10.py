#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path('/opt/AETHIEAOPSYS')
BODY = ROOT / 'WORKSPACE/codex/aether-chat-aevps'
TARGET = BODY / 'body/code_engine.py'
STATE = ROOT / 'STATE/aetherbot/creator-action-discipline'
EXPECTED_SHA256 = '5d34a427cfb8f0b467cd8a6486de2cc2d958c51b800964bb951432ec390cf849'
MARKER = '# AETHER_CREATOR_ACTION_DISCIPLINE_V10'

INSERT = r'''
# AETHER_CREATOR_ACTION_DISCIPLINE_V10
The active code scope root is already the working root for every creator action.
Do not emit a shell `cd` command. A standalone `cd` cannot persist between executor actions and is not an executor-supported command.
For discovery, use the native search and read actions directly with paths relative to the active code scope root.
Example: to inspect /opt/AETHIEAOPSYS/aevp/aevp_creator, use path "aevp/aevp_creator" in search/read rather than changing directories.
Use shell only for executor-supported commands when search/read are insufficient.
If EXECUTOR_RESULT_JSON reports that an action or command was rejected, do not repeat the same action. Choose a different executor-supported action using the returned result as the authoritative capability state.
'''


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def build_candidate(text: str) -> str:
    if MARKER in text:
        return text

    required = [
        '# AETHER_CREATOR_REUSE_FIRST_V2',
        '# AETHER_CREATOR_COMPLETION_TRUTH_V1',
        '# AETHER_CREATOR_ACTION_SCHEMA_V8',
        '# AETHER_CREATOR_DISCOVERY_BUDGET_V9',
        'EXECUTOR_RESULT_JSON',
    ]
    missing = [x for x in required if x not in text]
    if missing:
        raise RuntimeError('REQUIRED_MARKERS_MISSING=' + ','.join(missing))

    start = text.find('SYSTEM = r"""')
    if start < 0:
        raise RuntimeError('SYSTEM_PROMPT_START_NOT_FOUND')
    end = text.find('\n"""', start + len('SYSTEM = r"""'))
    if end < 0:
        raise RuntimeError('SYSTEM_PROMPT_END_NOT_FOUND')

    prompt = text[start:end]
    if '# AETHER_CREATOR_REUSE_FIRST_V2' not in prompt:
        raise RuntimeError('REUSE_MARKER_NOT_IN_SYSTEM_PROMPT')
    if '# AETHER_CREATOR_COMPLETION_TRUTH_V1' not in prompt:
        raise RuntimeError('TRUTH_MARKER_NOT_IN_SYSTEM_PROMPT')

    out = text[:end] + '\n' + INSERT.rstrip() + text[end:]
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

    print('AETHER CREATOR // ACTION DISCIPLINE V10')
    print(f'TARGET={TARGET}')
    print(f'CURRENT_SHA256={current}')
    print(f'EXPECTED_SHA256={EXPECTED_SHA256}')
    print(f'ALREADY_PATCHED={"YES" if MARKER in text else "NO"}')
    print('ACTIVE_ROOT=ALREADY_SET')
    print('SHELL_CD=DO_NOT_EMIT')
    print('DISCOVERY=SEARCH_READ_RELATIVE_PATHS')
    print('REJECTED_ACTION=DO_NOT_REPEAT')
    print('ACTION_SCHEMA_V8=KEPT')
    print('DISCOVERY_BUDGET_V9=KEPT')
    print('EXECUTOR=UNCHANGED')
    print('PATH_SCOPE=UNCHANGED')
    print('MODEL=UNCHANGED')
    print('MIDDLEWARE=UNCHANGED')
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
        'Do not emit a shell `cd` command.',
        'use path "aevp/aevp_creator" in search/read',
        'do not repeat the same action',
        '# AETHER_CREATOR_ACTION_SCHEMA_V8',
        '# AETHER_CREATOR_DISCOVERY_BUDGET_V9',
    ]
    missing = [x for x in required_final if x not in final]
    if missing:
        shutil.copy2(backup, TARGET)
        print('ROLLBACK=VERIFY_FAILED:' + ','.join(missing))
        return 8

    print('AETHER_CREATOR_ACTION_DISCIPLINE=V10')
    print('SHELL_CD=PROTOCOL_DISABLED')
    print('DISCOVERY_PATHS=RELATIVE_TO_ACTIVE_ROOT')
    print('REJECTED_ACTION_REPEAT=PROTOCOL_DISABLED')
    print('ACTION_SCHEMA_V8=KEPT')
    print('DISCOVERY_BUDGET_V9=KEPT')
    print('EXECUTOR_CHANGED=NO')
    print('PATH_SCOPE_CHANGED=NO')
    print('CODE_ENGINE_COMPILE=PASS')
    print(f'ENGINE_SHA256_NEW={sha256(TARGET)}')
    print(f'BACKUP_DIR={backup_dir}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
