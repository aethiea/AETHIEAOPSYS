#!/usr/bin/env python3
import os
from pathlib import Path
import re

ROOT = Path(os.environ["AETHIEA"])
TARGET = ROOT / "CORE" / "router.py"

src = TARGET.read_text(encoding="utf-8")

# --- 1. Remove any previously injected broken block ---
src = re.sub(
    r"# --- AENET FIRST ROUTES ---.*?return routes\.get\(name\)",
    "",
    src,
    flags=re.S
)

# --- 2. Clean any escaped newline artifacts ---
src = src.replace("\\n\\n", "\n\n")

# --- 3. Inject clean AENET-first resolver ---
patch = """
# --- AENET FIRST ROUTES ---
AENET = ROOT / "LAYERS" / "AENET"

def resolve_route(name: str):
    name = (name or "").lower().strip()

    # direct layer hits
    if name in ("network", "aenet", "aethernet"):
        return AENET

    if name == "cloudflare":
        return AENET / "CLOUDFLARE"

    # dynamic AENET subpaths
    candidate = AENET / name.upper()
    if candidate.exists():
        return candidate

    # fallback to existing route table
    routes = build_routes()
    return routes.get(name)
"""

# --- 4. Ensure only one resolve_route exists ---
if "def resolve_route(" in src:
    src = re.sub(r"def resolve_route\(.*?\n\s*return routes\.get\(name\)\n", "", src, flags=re.S)

# --- 5. Append clean version ---
src = src.strip() + "\n\n" + patch.strip() + "\n"

TARGET.write_text(src, encoding="utf-8")

print("PATCHED CLEAN → router.py (AENET-first, deduplicated)")
