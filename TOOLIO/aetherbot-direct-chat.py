#!/usr/bin/env python3

"""Bare `aetherbot` handoff to the canonical AETHER body.

Historical AEVPS evidence shows the original front door did not exec the
separate `aetherchat` client. It exported the AETHER workspace on PYTHONPATH and
ran `python3 -m body "$@"`. That body owns sessions, memory, receipts, mode
routing, `/open`, `/ground`, `/ops`, and `--latest` resume semantics.

The broader /usr/local/bin/aetherbot wrapper currently invokes this shim for its
bare-chat route and may inject a legacy model token (for example `qwen3:4b`).
That token belonged to the later direct-Ollama experiment, not to the canonical
body CLI, so this shim strips only a leading model-shaped compatibility token
before handing remaining CLI arguments to `python3 -m body`.

If AETHER :3936 is down, bootstrap only the two services required for ordinary
AETHER chat: the local llama.cpp middleware and `aether.service`. B43 remains
optional and is not auto-started for ordinary open chat.
"""

from __future__ import annotations

import os
from pathlib import Path
import socket
import subprocess
import sys
import time


AETHER_ROOT = Path(
    os.environ.get(
        "AETHER_CHAT_ROOT",
        "/opt/AETHIEAOPSYS/WORKSPACE/codex/aether-chat-aevps",
    )
).resolve()
AETHER_HOST = os.environ.get("AETHER_HOST", "127.0.0.1")
AETHER_PORT = int(os.environ.get("AETHER_PORT", "3936"))
BOOTSTRAP = os.environ.get("AETHERBOT_BOOTSTRAP", "1") not in {"0", "false", "False"}


def port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except OSError:
        return False


def start_unit(unit: str) -> bool:
    status = subprocess.run(
        ["systemctl", "is-active", "--quiet", unit],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if status.returncode == 0:
        return True

    print(f"[bootstrap] starting {unit}", flush=True)
    started = subprocess.run(
        ["systemctl", "start", unit],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return started.returncode == 0


def ensure_aether() -> bool:
    if port_open(AETHER_HOST, AETHER_PORT):
        return True

    if not BOOTSTRAP:
        return False

    if not start_unit("aeth-middleware-awareness.service"):
        print("ERROR: could not start local llama.cpp middleware", file=sys.stderr)
        return False

    if not start_unit("aether.service"):
        print("ERROR: could not start aether.service", file=sys.stderr)
        return False

    for _ in range(30):
        if port_open(AETHER_HOST, AETHER_PORT):
            print(f"[bootstrap] AETHER :{AETHER_PORT} online", flush=True)
            return True
        time.sleep(1)

    return False


def body_args(argv: list[str]) -> list[str]:
    """Drop only the legacy wrapper's injected direct-Ollama model token."""
    args = list(argv)
    if args and not args[0].startswith("-") and ":" in args[0]:
        args.pop(0)
    return args


def main() -> int:
    body_main = AETHER_ROOT / "body" / "__main__.py"
    if not body_main.is_file():
        print(f"ERROR: canonical AETHER body missing: {body_main}", file=sys.stderr)
        return 127

    if not ensure_aether():
        print(
            f"ERROR: AETHER service unavailable at {AETHER_HOST}:{AETHER_PORT}",
            file=sys.stderr,
        )
        print(
            "Inspect: systemctl status aether.service aeth-middleware-awareness.service --no-pager",
            file=sys.stderr,
        )
        return 69

    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(AETHER_ROOT) + ((":" + existing) if existing else "")

    argv = [sys.executable, "-m", "body", *body_args(sys.argv[1:])]
    os.execve(sys.executable, argv, env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
