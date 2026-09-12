#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

TARGET = Path('/opt/AETHIEAOPSYS/WORKSPACE/codex/aether-chat-aevps/body/code_engine.py')
EXPECTED_SHA256 = '781a934f1389feeaf7b6ee982b7c69efa093d54a8af759d98389f5db62deccca'
MARKER = '# AETHER_CREATOR_JSON_RAW_DECODE_V1'

OLD = '''    action = json.loads(text)\n\n    if not isinstance(action, dict):\n'''
NEW = '''    # AETHER_CREATOR_JSON_RAW_DECODE_V1\n    # The creator loop executes one authenticated tool action per step.\n    # Some local checkpoints emit several JSON objects in one response;\n    # decode the first object only, execute it, return the real tool result,\n    # then let AETHER choose the next action on the following model turn.\n    decoder = json.JSONDecoder()\n    action, _end = decoder.raw_decode(text)\n\n    if not isinstance(action, dict):\n'''


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    if not TARGET.is_file():
        raise SystemExit(f'STOP=TARGET_MISSING:{TARGET}')

    current = sha256(TARGET)
    text = TARGET.read_text(encoding='utf-8')
    already = MARKER in text

    print('AETHER CREATOR // MULTI-JSON PROTOCOL CUTOVER PLAN')
    print(f'TARGET={TARGET}')
    print(f'CURRENT_SHA256={current}')
    print(f'EXPECTED_PREPATCH_SHA256={EXPECTED_SHA256}')
    print(f'ALREADY_PATCHED={"YES" if already else "NO"}')
    print('PROTOCOL_MODE=ONE_REAL_ACTION_PER_STEP')
    print('BATCHED_MODEL_JSON=FIRST_OBJECT_ONLY')
    print('TOOL_IMPLEMENTATION_CHANGED=NO')
    print('AEVPS_SCOPE_CHANGED=NO')
    print('WRITE_GATE_CHANGED=NO')
    print('CODE_RECEIPTS_CHANGED=NO')

    if not args.apply:
        return 0

    if already:
        print('AETHER_CREATOR_JSON_PROTOCOL=ALREADY_PATCHED')
        return 0

    if current != EXPECTED_SHA256:
        raise SystemExit(f'STOP=UNEXPECTED_TARGET_SHA256:{current}')

    if text.count(OLD) != 1:
        raise SystemExit(f'STOP=PARSE_ANCHOR_COUNT:{text.count(OLD)}')

    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup_root = Path('/opt/AETHIEAOPSYS/STATE/aetherbot/creator-engine') / stamp
    backup_root.mkdir(parents=True, exist_ok=True)
    backup = backup_root / 'code_engine.py.before-jsonl'
    shutil.copy2(TARGET, backup)

    patched = text.replace(OLD, NEW, 1)
    TARGET.write_text(patched, encoding='utf-8')

    proc = subprocess.run(
        ['python3', '-m', 'py_compile', str(TARGET)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if proc.returncode != 0:
        shutil.copy2(backup, TARGET)
        raise SystemExit('STOP=COMPILE_FAILED_ROLLED_BACK\n' + proc.stdout)

    # Direct parser smoke test: two valid objects must return only the first.
    import importlib.util
    spec = importlib.util.spec_from_file_location('aether_code_engine_probe', TARGET)
    if spec is None or spec.loader is None:
        shutil.copy2(backup, TARGET)
        raise SystemExit('STOP=IMPORT_SPEC_FAILED_ROLLED_BACK')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    probe = mod.parse_action('{"action":"read","path":"README.md"}\n{"action":"final","message":"later"}')
    if probe.get('action') != 'read' or probe.get('path') != 'README.md':
        shutil.copy2(backup, TARGET)
        raise SystemExit(f'STOP=PARSER_PROBE_FAILED_ROLLED_BACK:{probe!r}')

    print('AETHER_CREATOR_JSON_PROTOCOL=RAW_DECODE_V1')
    print('MULTI_JSON_PROBE=PASS')
    print('CODE_ENGINE_COMPILE=PASS')
    print('PROTOCOL_MODE=ONE_REAL_ACTION_PER_STEP')
    print('TOOL_IMPLEMENTATION_CHANGED=NO')
    print('AEVPS_SCOPE_CHANGED=NO')
    print('WRITE_GATE_CHANGED=NO')
    print('CODE_RECEIPTS_CHANGED=NO')
    print(f'NEW_SHA256={sha256(TARGET)}')
    print(f'BACKUP={backup}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
