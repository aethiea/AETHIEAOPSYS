#!/usr/bin/env python3

"""Bare `aetherbot` handoff to the canonical AETHER chat client.

The full /usr/local/bin/aetherbot wrapper owns the broader command family. Its
bare-chat branch invokes this file. Do not duplicate AETHER's conversation,
session, memory, receipt, retrieval, or mode-routing logic here. Hand control to
the existing `aetherchat` client, which talks to the canonical AETHER service on
its configured local endpoint (historically 127.0.0.1:3936).

`aetherbody` remains the transcript/history viewer and is intentionally not used
as the interactive chat entry point.
"""

import os
import shutil
import sys


AETHERCHAT = os.environ.get("AETHERCHAT_CMD", "aetherchat")


def main() -> int:
    resolved = shutil.which(AETHERCHAT)
    if resolved is None:
        print(
            f"ERROR: canonical AETHER chat client {AETHERCHAT!r} not found in PATH",
            file=sys.stderr,
        )
        return 127

    os.execv(resolved, [AETHERCHAT])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
