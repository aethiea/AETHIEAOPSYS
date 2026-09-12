#!/usr/bin/env python3
from __future__ import annotations

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
STATE = ROOT / 'STATE/aetherbot/creator-turn-budget'
EXPECTED_SHA256 = 'f1a873cb07d6019a162b5adfd8404d3e4fd92ad633eedc06b3be9831e87a0dba'
MARKER = '# AETHER_CREATOR_TURN_BUDGET_V7'
OLD_BUDGET = '            "max_tokens": 1800,\n'
NEW_BUDGET = (
    f'            {MARKER}\n'
    '            "max_tokens": 512,\n'
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def build_candidate(text: str) -> str:
    if MARKER in text:
        return text

    if text.count(OLD_BUDGET) != 1:
        raise RuntimeError(f'MAX_TOKEN_ANCHOR_COUNT={text.count(OLD_BUDGET)}')

    if '# AETHER_CREATOR_STRUCTURED_JSON_V1' not in text:
        raise RuntimeError('STRUCTURED_JSON_MARKER_MISSING')
    if '# AETHER_CREATOR_REUSE_FIRST_V2' not in text:
        raise RuntimeError('REUSE_FIRST_MARKER_MISSING')

    out = text.replace(OLD_BUDGET, NEW_BUDGET, 1)

    pattern = re.compile(r'(?m)^(?P<i>[ \t]*)raw = ollama\(messages\)[ \t]*$')
    matches = list(pattern.finditer(out))
    if len(matches) != 1:
        raise RuntimeError(f'OLLAMA_CALL_COUNT={len(matches)}')

    m = matches[0]
    indent = m.group('i')
    replacement = (
        f'{indent}try:\n'
        f'{indent}    raw = ollama(messages)\n'
        f'{indent}except TimeoutError:\n'
        f'{indent}    print("MODEL_TIMEOUT // creator inference exceeded transport budget")\n'
        f'{indent}    return 70'
    )
    out = out[:m.start()] + replacement + out[m.end():]
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

    print('AETHER CREATOR // TURN BUDGET V7')
    print(f'TARGET={TARGET}')
    print(f'CURRENT_SHA256={current}')
    print(f'EXPECTED_SHA256={EXPECTED_SHA256}')
    print(f'ALREADY_PATCHED={"YES" if MARKER in text else "NO"}')
    print('CREATOR_MAX_TOKENS=512')
    print('HTTP_TIMEOUT=UNCHANGED_480S')
    print('TIMEOUT_CRASH=CONVERT_TO_RETURN_70')
    print('REUSE_FIRST=UNCHANGED')
    print('AUTO_ROUTE=UNCHANGED')
    print('EXECUTOR=UNCHANGED')
    print('PATH_SCOPE=UNCHANGED')
    print('RECEIPTS=UNCHANGED')
    print('MODEL=UNCHANGED')
    print('MIDDLEWARE=UNCHANGED')

    if MARKER in text:
        return 0
    if current != EXPECTED_SHA256:
        print('STOP=UNEXPECTED_ENGINE_SHA256')
        return 4

    try:
        candidate = build_candidate(text)
    except RuntimeError as exc:
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
    required = [
        MARKER,
        '"max_tokens": 512,',
        'except TimeoutError:',
        '# AETHER_CREATOR_STRUCTURED_JSON_V1',
        '# AETHER_CREATOR_REUSE_FIRST_V2',
        'allow_write: bool = True',
        'EXECUTOR_RESULT_JSON',
    ]
    missing = [x for x in required if x not in final]
    if missing:
        shutil.copy2(backup, TARGET)
        print('ROLLBACK=VERIFY_FAILED:' + ','.join(missing))
        return 8

    print('AETHER_CREATOR_TURN_BUDGET=V7')
    print('CREATOR_MAX_TOKENS=512')
    print('HTTP_TIMEOUT=480S_UNCHANGED')
    print('TIMEOUT_PROCESS_CRASH=FIXED')
    print('CODE_ENGINE_COMPILE=PASS')
    print(f'ENGINE_SHA256_NEW={sha256(TARGET)}')
    print(f'BACKUP_DIR={backup_dir}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
