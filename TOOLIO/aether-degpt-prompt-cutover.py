#!/usr/bin/env python3
"""Remove GPT/OpenAI-style policy/refusal language from AETHER prompt membranes.

This patch is intentionally narrow. It changes only:
- src/aether_chat.py -> OPEN_SYSTEM
- body/code_engine.py -> creator SYSTEM prompt

It does not change llama.cpp launch flags, model checkpoint, AEMCP, vRAG, B43,
filesystem/path scope enforcement, shell/tool validation, receipts, systemd,
or executor behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/opt/AETHIEAOPSYS")
BODY = ROOT / "WORKSPACE/codex/aether-chat-aevps"
CHAT = BODY / "src/aether_chat.py"
ENGINE = BODY / "body/code_engine.py"
STATE = ROOT / "STATE/aetherbot/degpt-prompts"

EXPECTED_CHAT_SHA256 = "35820fe69964e7a05fdf8e3504e1604d42f9a7a1429061cebfc9b5208ae850d9"
EXPECTED_ENGINE_SHA256 = "e5c0c0f4cc20a139b20533bc67b075d919ecfbdd0cfa79540200586c02e9074f"

OPEN_MARKER = "# AETHER_OPEN_LOCAL_IDENTITY_V3"
CREATOR_MARKER = "# AETHER_CREATOR_LOCAL_PROTOCOL_V2"

OPEN_BLOCK = '''# AETHER_OPEN_LOCAL_IDENTITY_V3
OPEN_SYSTEM = """\\
You are AETHER, the local conversational intelligence of AETHIEAOPSYS.
Converse directly with the operator using relevant conversation history.
"""


'''

CREATOR_BLOCK = r'''# AETHER_CREATOR_LOCAL_PROTOCOL_V2
SYSTEM = r"""
You are AETHER using your native AEVPS creator and programming capability.

Emit exactly one JSON action per creator turn using an executor-supported action shape, including:
{"action":"shell","command":"..."}
{"action":"read","path":"relative/path"}
{"action":"search","path":"relative/path","pattern":"literal text"}
{"action":"write","path":"relative/path","content":"..."}
{"action":"final","message":"..."}

EXECUTOR_RESULT_JSON is the runtime result for the preceding action.
Use those runtime results as execution state and continue until the operator's task is complete.
"""'''

RAIL_TERMS = (
    "openai",
    "chatgpt",
    "policy",
    "policies",
    "safety",
    "guideline",
    "guidelines",
    "refuse",
    "refusal",
    "cannot assist",
    "can't help",
    "harmful",
    "ethical",
    "compliance",
    "guardrail",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def prompt_rail_hits(text: str) -> list[str]:
    low = text.lower()
    return [term for term in RAIL_TERMS if term in low]


def replace_open(source: str) -> str:
    # Replace only OPEN_SYSTEM, stopping before GROUND_SYSTEM.
    pattern = re.compile(
        r'# AETHER_OPEN_[^\n]*\nOPEN_SYSTEM = """\\\n.*?\n"""\n\n\n(?=GROUND_SYSTEM = """\\\n)',
        re.S,
    )
    matches = list(pattern.finditer(source))
    if len(matches) == 1:
        return pattern.sub(OPEN_BLOCK, source, count=1)

    # Current V2 exact fallback.
    token = '# AETHER_OPEN_IDENTITY_ONLY_V2\nOPEN_SYSTEM = """\\\n'
    start = source.find(token)
    if start < 0:
        raise RuntimeError(f"OPEN_SYSTEM_BLOCK_COUNT:{len(matches)}")
    ground = source.find('GROUND_SYSTEM = """\\\n', start)
    if ground < 0:
        raise RuntimeError("GROUND_SYSTEM_START_NOT_FOUND")
    return source[:start] + OPEN_BLOCK + source[ground:]


def replace_creator(source: str) -> str:
    pattern = re.compile(r'(?:# AETHER_CREATOR_AUTONOMY_V1\n)?SYSTEM = r"""\n.*?\n"""', re.S)
    matches = list(pattern.finditer(source))
    if len(matches) != 1:
        raise RuntimeError(f"CREATOR_SYSTEM_BLOCK_COUNT:{len(matches)}")
    return pattern.sub(CREATOR_BLOCK, source, count=1)


def extract_open(text: str) -> str:
    start = text.find("OPEN_SYSTEM =")
    end = text.find("GROUND_SYSTEM =", start)
    if start < 0 or end < 0:
        raise RuntimeError("OPEN_PROMPT_EXTRACT_FAILED")
    return text[start:end]


def extract_creator(text: str) -> str:
    m = re.search(r'SYSTEM = r"""\n(.*?)\n"""', text, re.S)
    if not m:
        raise RuntimeError("CREATOR_PROMPT_EXTRACT_FAILED")
    return m.group(0)


def compile_file(path: Path) -> tuple[int, str]:
    cp = subprocess.run(
        [sys.executable, "-m", "py_compile", str(path)],
        cwd=str(BODY),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return cp.returncode, cp.stdout


def plan() -> int:
    if not CHAT.is_file() or not ENGINE.is_file():
        print("STOP=CANONICAL_PROMPT_FILES_MISSING")
        return 2
    chat_text = CHAT.read_text(encoding="utf-8")
    engine_text = ENGINE.read_text(encoding="utf-8")
    print("AETHER // DE-GPT PROMPT CUTOVER PLAN")
    print(f"CHAT_SHA256={sha256(CHAT)}")
    print(f"EXPECTED_CHAT_SHA256={EXPECTED_CHAT_SHA256}")
    print(f"ENGINE_SHA256={sha256(ENGINE)}")
    print(f"EXPECTED_ENGINE_SHA256={EXPECTED_ENGINE_SHA256}")
    print("TARGET=OPEN_SYSTEM+CREATOR_SYSTEM_ONLY")
    print("MIDDLEWARE_FLAGS_CHANGED=NO")
    print("MODEL_CHANGED=NO")
    print("TOOL_EXECUTOR_CHANGED=NO")
    print("PATH_SCOPE_CHANGED=NO")
    print("RECEIPTS_CHANGED=NO")
    print("OPEN_PROMPT_RAIL_HITS=" + (",".join(prompt_rail_hits(extract_open(chat_text))) or "NONE"))
    print("CREATOR_PROMPT_RAIL_HITS=" + (",".join(prompt_rail_hits(extract_creator(engine_text))) or "NONE"))
    return 0


def apply() -> int:
    if os.geteuid() != 0:
        print("STOP=ROOT_REQUIRED")
        return 2
    if not CHAT.is_file() or not ENGINE.is_file():
        print("STOP=CANONICAL_PROMPT_FILES_MISSING")
        return 3

    chat_text = CHAT.read_text(encoding="utf-8")
    engine_text = ENGINE.read_text(encoding="utf-8")

    if OPEN_MARKER in chat_text and CREATOR_MARKER in engine_text:
        print("AETHER_DEGPT_PROMPTS=ALREADY_PATCHED")
        return 0

    chat_hash = sha256(CHAT)
    engine_hash = sha256(ENGINE)
    if chat_hash != EXPECTED_CHAT_SHA256:
        print(f"STOP=UNEXPECTED_CHAT_SHA256:{chat_hash}")
        return 4
    if engine_hash != EXPECTED_ENGINE_SHA256:
        print(f"STOP=UNEXPECTED_ENGINE_SHA256:{engine_hash}")
        return 5

    try:
        chat_candidate = replace_open(chat_text)
        engine_candidate = replace_creator(engine_text)
        open_hits = prompt_rail_hits(extract_open(chat_candidate))
        creator_hits = prompt_rail_hits(extract_creator(engine_candidate))
    except RuntimeError as exc:
        print(f"STOP={exc}")
        return 6

    if open_hits or creator_hits:
        print("STOP=PROMPT_RAIL_TERMS_REMAIN")
        print("OPEN=" + ",".join(open_hits))
        print("CREATOR=" + ",".join(creator_hits))
        return 7

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    backup = STATE / stamp
    backup.mkdir(parents=True, exist_ok=True)
    chat_backup = backup / "aether_chat.py.before-degpt"
    engine_backup = backup / "code_engine.py.before-degpt"
    shutil.copy2(CHAT, chat_backup)
    shutil.copy2(ENGINE, engine_backup)

    chat_tmp = backup / "aether_chat.py.candidate"
    engine_tmp = backup / "code_engine.py.candidate"
    chat_tmp.write_text(chat_candidate, encoding="utf-8")
    engine_tmp.write_text(engine_candidate, encoding="utf-8")

    for candidate in (chat_tmp, engine_tmp):
        rc, out = compile_file(candidate)
        if rc != 0:
            print(f"STOP=CANDIDATE_COMPILE_FAILED:{candidate.name}")
            print(out.rstrip())
            return 8

    CHAT.write_text(chat_candidate, encoding="utf-8")
    ENGINE.write_text(engine_candidate, encoding="utf-8")

    for live in (CHAT, ENGINE):
        rc, out = compile_file(live)
        if rc != 0:
            shutil.copy2(chat_backup, CHAT)
            shutil.copy2(engine_backup, ENGINE)
            print(f"ROLLBACK=LIVE_COMPILE_FAILED:{live.name}")
            print(out.rstrip())
            return 9

    # OPEN prompt is owned by aether.service; reload that service only.
    subprocess.run(["systemctl", "restart", "aether.service"], check=True)
    health = subprocess.run(
        ["curl", "-fsS", "http://127.0.0.1:3936/health"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if health.returncode != 0:
        shutil.copy2(chat_backup, CHAT)
        shutil.copy2(engine_backup, ENGINE)
        subprocess.run(["systemctl", "restart", "aether.service"], check=False)
        print("ROLLBACK=AETHER_HEALTH_FAILED")
        return 10

    final_open = extract_open(CHAT.read_text(encoding="utf-8"))
    final_creator = extract_creator(ENGINE.read_text(encoding="utf-8"))
    if prompt_rail_hits(final_open) or prompt_rail_hits(final_creator):
        shutil.copy2(chat_backup, CHAT)
        shutil.copy2(engine_backup, ENGINE)
        subprocess.run(["systemctl", "restart", "aether.service"], check=False)
        print("ROLLBACK=RAIL_TERM_VERIFY_FAILED")
        return 11

    print("AETHER_DEGPT_PROMPTS=V1")
    print("OPEN_SYSTEM=LOCAL_IDENTITY_ONLY")
    print("CREATOR_SYSTEM=LOCAL_PROTOCOL_ONLY")
    print("GPT_OPENAI_POLICY_LANGUAGE=NONE_IN_TARGET_PROMPTS")
    print("REFUSAL_LANGUAGE=NONE_IN_TARGET_PROMPTS")
    print("MIDDLEWARE_FLAGS_CHANGED=NO")
    print("MODEL_CHANGED=NO")
    print("TOOL_EXECUTOR_CHANGED=NO")
    print("PATH_SCOPE_CHANGED=NO")
    print("RECEIPTS_CHANGED=NO")
    print("AETHER_3936=ONLINE")
    print(f"CHAT_SHA256_NEW={sha256(CHAT)}")
    print(f"ENGINE_SHA256_NEW={sha256(ENGINE)}")
    print(f"BACKUP_DIR={backup}")
    return 0


def rollback() -> int:
    if os.geteuid() != 0:
        print("STOP=ROOT_REQUIRED")
        return 2
    backups = sorted(STATE.glob("*/aether_chat.py.before-degpt"), reverse=True)
    if not backups:
        print("STOP=NO_DEGPT_BACKUP")
        return 3
    chat_backup = backups[0]
    engine_backup = chat_backup.parent / "code_engine.py.before-degpt"
    if not engine_backup.is_file():
        print("STOP=ENGINE_BACKUP_MISSING")
        return 4
    shutil.copy2(chat_backup, CHAT)
    shutil.copy2(engine_backup, ENGINE)
    subprocess.run([sys.executable, "-m", "py_compile", str(CHAT), str(ENGINE)], cwd=str(BODY), check=True)
    subprocess.run(["systemctl", "restart", "aether.service"], check=True)
    print(f"ROLLBACK=PASS:{chat_backup.parent}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--apply", action="store_true")
    g.add_argument("--rollback", action="store_true")
    args = ap.parse_args()
    if args.apply:
        return apply()
    if args.rollback:
        return rollback()
    return plan()


if __name__ == "__main__":
    raise SystemExit(main())
