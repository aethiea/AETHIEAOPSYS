#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path('/opt/AETHIEAOPSYS')
BODY = ROOT / 'WORKSPACE/codex/aether-chat-aevps'
TARGET = BODY / 'body/code_engine.py'
STATE = ROOT / 'STATE/aetherbot/creator-schema-protocol'
EXPECTED_SHA256 = '4aaafcd0d3b40bc8a3ba16ca2bf032c028c9e95d19dd37fe8ae8054997484297'
MARKER = '# AETHER_CREATOR_ACTION_SCHEMA_V8'
MODEL = 'mistral_7b_uncensored.Q4_K_M'
LLAMA_URL = 'http://127.0.0.1:3926/v1/chat/completions'

OLD_MODEL_LINE = 'MODEL = "mistral_7b_uncensored.Q4_K_M"\n'
OLD_RESPONSE_FORMAT = '            "response_format": {"type": "json_object"},\n'
OLD_BUDGET = '            "max_tokens": 512,\n'
NEW_BUDGET = '            "max_tokens": 1024,\n'

SCHEMA_BLOCK = r'''# AETHER_CREATOR_ACTION_SCHEMA_V8
CREATOR_ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["shell", "read", "search", "write", "final"],
        },
        "command": {"type": "string"},
        "path": {"type": "string"},
        "pattern": {"type": "string"},
        "content": {"type": "string"},
        "message": {"type": "string"},
    },
    "required": ["action"],
    "additionalProperties": False,
}
'''

NEW_RESPONSE_FORMAT = (
    '            "response_format": {\n'
    '                "type": "json_object",\n'
    '                "schema": CREATOR_ACTION_SCHEMA,\n'
    '            },\n'
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def schema_probe() -> tuple[bool, str]:
    schema = {
        'type': 'object',
        'properties': {
            'action': {
                'type': 'string',
                'enum': ['shell', 'read', 'search', 'write', 'final'],
            },
            'command': {'type': 'string'},
            'path': {'type': 'string'},
            'pattern': {'type': 'string'},
            'content': {'type': 'string'},
            'message': {'type': 'string'},
        },
        'required': ['action'],
        'additionalProperties': False,
    }
    payload = {
        'model': 'local',
        'messages': [
            {
                'role': 'system',
                'content': 'Emit exactly one creator action object.',
            },
            {
                'role': 'user',
                'content': 'Finish immediately with message probe.',
            },
        ],
        'stream': False,
        'temperature': 0.0,
        'max_tokens': 128,
        'response_format': {
            'type': 'json_object',
            'schema': schema,
        },
    }
    req = urllib.request.Request(
        LLAMA_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.load(r)
        raw = data['choices'][0]['message']['content'].strip()
        obj = json.loads(raw)
        if not isinstance(obj, dict):
            return False, f'NON_OBJECT:{raw[:300]}'
        if obj.get('action') not in {'shell', 'read', 'search', 'write', 'final'}:
            return False, f'BAD_ACTION:{raw[:300]}'
        return True, raw[:300]
    except Exception as exc:
        return False, repr(exc)


def build_candidate(text: str) -> str:
    if MARKER in text:
        return text

    if text.count(OLD_MODEL_LINE) != 1:
        raise RuntimeError(f'MODEL_ANCHOR_COUNT={text.count(OLD_MODEL_LINE)}')
    if text.count(OLD_RESPONSE_FORMAT) != 1:
        raise RuntimeError(
            f'RESPONSE_FORMAT_ANCHOR_COUNT={text.count(OLD_RESPONSE_FORMAT)}'
        )
    if text.count(OLD_BUDGET) != 1:
        raise RuntimeError(f'BUDGET_ANCHOR_COUNT={text.count(OLD_BUDGET)}')

    required = [
        '# AETHER_CREATOR_STRUCTURED_JSON_V1',
        '# AETHER_CREATOR_REUSE_FIRST_V2',
        '# AETHER_CREATOR_COMPLETION_TRUTH_V1',
        '# AETHER_CREATOR_TURN_BUDGET_V7',
        'EXECUTOR_RESULT_JSON',
        'allow_write: bool = True',
    ]
    missing = [x for x in required if x not in text]
    if missing:
        raise RuntimeError('REQUIRED_MARKERS_MISSING=' + ','.join(missing))

    out = text.replace(
        OLD_MODEL_LINE,
        OLD_MODEL_LINE + '\n' + SCHEMA_BLOCK + '\n',
        1,
    )
    out = out.replace(OLD_RESPONSE_FORMAT, NEW_RESPONSE_FORMAT, 1)
    out = out.replace(OLD_BUDGET, NEW_BUDGET, 1)
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

    print('AETHER CREATOR // ACTION SCHEMA V8')
    print(f'TARGET={TARGET}')
    print(f'CURRENT_SHA256={current}')
    print(f'EXPECTED_SHA256={EXPECTED_SHA256}')
    print(f'ALREADY_PATCHED={"YES" if MARKER in text else "NO"}')
    print('CREATOR_OUTPUT=SCHEMA_CONSTRAINED_JSON')
    print('ACTION_ENUM=shell,read,search,write,final')
    print('CREATOR_MAX_TOKENS=1024')
    print('HTTP_TIMEOUT=480S_UNCHANGED')
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

    ok, detail = schema_probe()
    print(f'LLAMA_CPP_ACTION_SCHEMA_PROBE={"PASS" if ok else "FAIL"}')
    print(f'PROBE_RESPONSE={detail}')
    if not ok:
        print('STOP=SCHEMA_PROBE_FAILED')
        return 5

    try:
        candidate = build_candidate(text)
    except RuntimeError as exc:
        print(f'STOP=CANDIDATE_BUILD:{exc}')
        return 6

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
        return 7

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
        return 8

    final = TARGET.read_text(encoding='utf-8')
    required_final = [
        MARKER,
        '"schema": CREATOR_ACTION_SCHEMA,',
        '"max_tokens": 1024,',
        '# AETHER_CREATOR_REUSE_FIRST_V2',
        '# AETHER_CREATOR_COMPLETION_TRUTH_V1',
        'except TimeoutError:',
        'EXECUTOR_RESULT_JSON',
    ]
    missing = [x for x in required_final if x not in final]
    if missing:
        shutil.copy2(backup, TARGET)
        print('ROLLBACK=VERIFY_FAILED:' + ','.join(missing))
        return 9

    print('AETHER_CREATOR_ACTION_SCHEMA=V8')
    print('LLAMA_CPP_ACTION_SCHEMA_PROBE=PASS')
    print('CREATOR_OUTPUT=SCHEMA_CONSTRAINED_JSON')
    print('PROMPT_ECHO_CANNOT_BE_VALID_ACTION=TRUE')
    print('CREATOR_MAX_TOKENS=1024')
    print('TIMEOUT_HANDLER=KEPT')
    print('CODE_ENGINE_COMPILE=PASS')
    print(f'ENGINE_SHA256_NEW={sha256(TARGET)}')
    print(f'BACKUP_DIR={backup_dir}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
