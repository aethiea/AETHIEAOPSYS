#!/usr/bin/env python3

"""Bare `aetherbot` handoff to the canonical AETHER chat client.

The full /usr/local/bin/aetherbot wrapper owns the broader command family. Its
bare-chat branch invokes this file. Do not duplicate AETHER's conversation,
session, memory, receipt, retrieval, or mode-routing logic here. Hand control to
the existing `aetherchat` client, which talks to the canonical AETHER service on
its configured local endpoint (historically 127.0.0.1:3936).

If the canonical AETHER service is not listening, restore the two services needed
for ordinary local chat: the llama.cpp middleware and AETHER itself. B43-RU5 is
not started automatically because ordinary chat does not require multi-agent
routing. `aetherbody` remains the transcript/history viewer.
"""

import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request


AETHERCHAT = os.environ.get("AETHERCHAT_CMD", "aetherchat")
AETHER_HEALTH = os.environ.get("AETHER_HEALTH_URL", "http://127.0.0.1:3936/health")
LLAMA_UNIT = os.environ.get("AETHER_LLAMA_UNIT", "aeth-middleware-awareness.service")
AETHER_UNIT = os.environ.get("AETHER_SERVICE_UNIT", "aether.service")


def healthy() -> bool:
    try:
        with urllib.request.urlopen(AETHER_HEALTH, timeout=2) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def unit_active(unit: str) -> bool:
    return subprocess.run(
        ["systemctl", "is-active", "--quiet", unit],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def start_unit(unit: str) -> bool:
    if unit_active(unit):
        return True

    print(f"[bootstrap] starting {unit}")
    result = subprocess.run(
        ["systemctl", "start", unit],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stdout.strip()
        print(f"ERROR: failed to start {unit}: {detail}", file=sys.stderr)
        return False
    return unit_active(unit)


def ensure_aether() -> bool:
    if healthy():
        return True

    # Original working AETHER used both the local llama.cpp middleware and
    # aether.service. Restore only those normal-chat dependencies here.
    if not start_unit(LLAMA_UNIT):
        return False
    if not start_unit(AETHER_UNIT):
        return False

    for _ in range(30):
        if healthy():
            print("[bootstrap] AETHER :3936 online")
            return True
        time.sleep(1)

    print(
        f"ERROR: {AETHER_UNIT} started but {AETHER_HEALTH} did not become healthy",
        file=sys.stderr,
    )
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
        return 1

    os.execv(resolved, [AETHERCHAT])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
