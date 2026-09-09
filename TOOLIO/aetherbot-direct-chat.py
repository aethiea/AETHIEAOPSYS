#!/usr/bin/env python3

"""Bare aetherbot handoff to the canonical AETHER chat body.

The full /usr/local/bin/aetherbot wrapper owns command-family routing.  Its bare
chat branch invokes this file.  Do not duplicate AETHER's conversation, session,
memory, receipt, or mode router here; hand control back to the canonical
`aetherbody --latest` human window instead.
"""

import os
import shutil
import sys


AETHERBODY = os.environ.get("AETHERBODY_CMD", "aetherbody")


def main() -> int:
    resolved = shutil.which(AETHERBODY)
    if resolved is None:
        print(
            f"ERROR: canonical AETHER client {AETHERBODY!r} not found in PATH",
            file=sys.stderr,
        )
        return 127

    os.execv(resolved, [AETHERBODY, "--latest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
