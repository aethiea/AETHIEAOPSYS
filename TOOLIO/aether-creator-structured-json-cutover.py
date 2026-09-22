#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import urllib.request

TARGET = Path('/opt/AETHIEAOPSYS/WORKSPACE/codex/aether-chat-aevps/body/code_engine.py')
EXPECTED_SHA256 = 'dfe190c7c3d76145be7740fa479812bd760939eebf469dd7723d52928f31a98a'
MARKER = '# AETHER_CREATOR_STRUCTURED_JSON_V1'
LLAMA_URL = 'http://127.0.0.1:3926/v1/chat/completions'

PAYLOAD_ANCHOR = '''            "stream": False,\n            "temperature": 0.1,\n            "max_tokens": 1800,\n'''
PAYLOAD_PATCH = '''            "stream": False,\n            "temperature": 0.1,\n            "max_tokens": 1800,\n            # AETHER_CREATOR_STRUCTURED_JSON_V1\n            # llama.cpp constrains each creator turn to one JSON object.\n            "response_format": {"type": "json_object"},\n'''

RESULT_LABEL_OLD = '"TOOL_RESULT:\\n"'
RESULT_LABEL_NEW = '"EXECUTOR_RESULT_JSON:\\n"'
CONTINUE_OLD = '+ "\\nContinue the task."'
CONTINUE_NEW = '''+ (\n                        "\\nThe object above is the real executor result for your previous action."\n                        " Return exactly ONE NEW JSON action object."\n                        " Do not output prose, do not imitate EXECUTOR_RESULT_JSON,"\n                        " and do not repeat an action that already succeeded unless"\n                        " repeating it is necessary to complete the task."\n                    )'''


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def structured_probe() -> tuple[bool, str]:
    payload = {
        'model': 'local',
        'messages': [
            {
                'role': 'system',
                'content': 'Return one JSON object with keys action and message.',
            },
            {
                'role': 'user',
                'content': 'Set action to final and message to probe.',
            },
        ],
        'stream': False,
        'temperature': 0.0,
        'max_tokens': 96,
        'response_format': {'type': 'json_object'},
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
        content = data['choices'][0]['message']['content'].strip()
        obj = json.loads(content)
        if not isinstance(obj, dict):
            return False, f'NON_OBJECT:{content[:300]}'
        return True, content[:300]
    except Exception as exc:
        return False, repr(exc)


def build_candidate(text: str) -> str:
    if MARKER in text:
        return text
    if text.count(PAYLOAD_ANCHOR) != 1:
        raise RuntimeError(f'PAYLOAD_ANCHOR_COUNT:{text.count(PAYLOAD_ANCHOR)}')
    if text.count(RESULT_LABEL_OLD) != 1:
        raise RuntimeError(f'RESULT_LABEL_COUNT:{text.count(RESULT_LABEL_OLD)}')
    if text.count(CONTINUE_OLD) != 1:
        raise RuntimeError(f'CONTINUE_ANCHOR_COUNT:{text.count(CONTINUE_OLD)}')

    out = text.replace(PAYLOAD_ANCHOR, PAYLOAD_PATCH, 1)
    out = out.replace(RESULT_LABEL_OLD, RESULT_LABEL_NEW, 1)
    out = out.replace(CONTINUE_OLD, CONTINUE_NEW, 1)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    if not TARGET.is_file():
        raise SystemExit(f'STOP=TARGET_MISSING:{TARGET}')

    current = sha256(TARGET)
    text = TARGET.read_text(encoding='utf-8')
    already = MARKER in text

    print('AETHER CREATOR // STRUCTURED JSON CUTOVER PLAN')
    print(f'TARGET={TARGET}')
    print(f'CURRENT_SHA256={current}')
    print(f'EXPECTED_PREPATCH_SHA256={EXPECTED_SHA256}')
    print(f'ALREADY_PATCHED={"YES" if already else "NO"}')
    print('CREATOR_OUTPUT=LLAMA_CPP_JSON_OBJECT')
    print('EXECUTOR_RESULT_LABEL=EXECUTOR_RESULT_JSON')
    print('PROTOCOL_MODE=ONE_REAL_ACTION_PER_STEP')
    print('TOOL_IMPLEMENTATION_CHANGED=NO')
    print('AEVPS_SCOPE_CHANGED=NO')
    print('WRITE_GATE_CHANGED=NO')
    print('CODE_RECEIPTS_CHANGED=NO')

    if not args.apply:
        return 0

    if already:
        print('AETHER_CREATOR_STRUCTURED_JSON=ALREADY_PATCHED')
        return 0

    if current != EXPECTED_SHA256:
        raise SystemExit(f'STOP=UNEXPECTED_TARGET_SHA256:{current}')

    ok, detail = structured_probe()
    if not ok:
        raise SystemExit('STOP=LLAMA_CPP_RESPONSE_FORMAT_PROBE_FAILED:' + detail)
    print('LLAMA_CPP_RESPONSE_FORMAT_PROBE=PASS')

    try:
        patched = build_candidate(text)
    except RuntimeError as exc:
        raise SystemExit('STOP=' + str(exc))

    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup_root = Path('/opt/AETHIEAOPSYS/STATE/aetherbot/creator-engine') / stamp
    backup_root.mkdir(parents=True, exist_ok=True)
    backup = backup_root / 'code_engine.py.before-structured-json'
    shutil.copy2(TARGET, backup)

    candidate = backup_root / 'code_engine.py.candidate'
    candidate.write_text(patched, encoding='utf-8')
    check = subprocess.run(
        ['python3', '-m', 'py_compile', str(candidate)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if check.returncode != 0:
        raise SystemExit('STOP=CANDIDATE_COMPILE_FAILED\n' + check.stdout)

    TARGET.write_text(patched, encoding='utf-8')
    check = subprocess.run(
        ['python3', '-m', 'py_compile', str(TARGET)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if check.returncode != 0:
        shutil.copy2(backup, TARGET)
        raise SystemExit('STOP=LIVE_COMPILE_FAILED_ROLLED_BACK\n' + check.stdout)

    # Parser remains tolerant, but constrained inference should now produce
    # a clean single object before parse_action sees the content.
    import importlib.util
    spec = importlib.util.spec_from_file_location('aether_code_engine_structured_probe', TARGET)
    if spec is None or spec.loader is None:
        shutil.copy2(backup, TARGET)
        raise SystemExit('STOP=IMPORT_SPEC_FAILED_ROLLED_BACK')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    parsed = mod.parse_action('{"action":"final","message":"probe"}')
    if parsed.get('action') != 'final':
        shutil.copy2(backup, TARGET)
        raise SystemExit('STOP=PARSER_PROBE_FAILED_ROLLED_BACK')

    print('AETHER_CREATOR_STRUCTURED_JSON=V1')
    print('CREATOR_OUTPUT=LLAMA_CPP_JSON_OBJECT')
    print('EXECUTOR_RESULT_LABEL=EXECUTOR_RESULT_JSON')
    print('PROTOCOL_MODE=ONE_REAL_ACTION_PER_STEP')
    print('PARSER_PROBE=PASS')
    print('CODE_ENGINE_COMPILE=PASS')
    print('TOOL_IMPLEMENTATION_CHANGED=NO')
    print('AEVPS_SCOPE_CHANGED=NO')
    print('WRITE_GATE_CHANGED=NO')
    print('CODE_RECEIPTS_CHANGED=NO')
    print(f'NEW_SHA256={sha256(TARGET)}')
    print(f'BACKUP={backup}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
