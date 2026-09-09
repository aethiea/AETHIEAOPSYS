#!/usr/bin/env python3

"""Bare `aetherbot` handoff to the canonical AETHER chat client.

The full /usr/local/bin/aetherbot wrapper owns the broader command family. Its
bare-chat branch invokes this file. Do not duplicate AETHER's conversation,
session, memory, receipt, retrieval, or mode-routing logic here. Hand control to
the existing `aetherchat` client, which talks to the canonical AETHER service on
its configured local endpoint (historically 127.0.0.1:3936).

`aetherbody` remains the transcript/history viewer and is intentionally not used
as the interactive chat entry point.

If the canonical service is down, this shim may bootstrap only the two services
required for ordinary AETHER chat: the local llama.cpp middleware and
`aether.service`. B43 is deliberately not auto-started for ordinary open chat.

If the live AETHER source has drifted from the historically proven open-mode
source set, use `TOOLIO/aether-restore-open-mode.py` from this branch. That
restorer is fail-closed and will only install byte-for-byte historical files that
match the recorded known-good SHA256 values.
"""

import os
import shutil
import socket
import subprocess
import sys
import time


AETHERCHAT = os.environ.get("AETHERCHAT_CMD", "aetherchat")
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

    # Historical working AETHER ordinary-chat baseline had both of these
    # services active. B43 remains optional and is not forced into open chat.
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


def main() -> int:
    resolved = shutil.which(AETHERCHAT)
    if resolved is None:
        print(
            f"ERROR: canonical AETHER chat client {AETHERCHAT!r} not found in PATH",
            file=sys.stderr,
        )
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

    os.execv(resolved, [AETHERCHAT])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
