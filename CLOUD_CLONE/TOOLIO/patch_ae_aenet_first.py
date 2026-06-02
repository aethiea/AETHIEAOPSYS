#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "CORE" / "router.py"

if not TARGET.exists():
    print(f"ERROR: {TARGET} not found")
    raise SystemExit(1)

src = TARGET.read_text(encoding="utf-8")

patch = '''
# --- AENET FIRST ROUTES ---
AENET = ROOT / "LAYERS" / "AENET"

def resolve_route(name: str):
    name = (name or "").lower().strip()

    if name in ("network", "aenet", "aethernet"):
        return AENET

    if name == "cloudflare":
        return AENET / "CLOUDFLARE"

    candidate = AENET / name.upper()
    if candidate.exists():
        return candidate

    routes = build_routes()
    return routes.get(name)
'''

if "AENET FIRST ROUTES" not in src:
    src += "\\n\\n" + patch

TARGET.write_text(src, encoding="utf-8")
print("PATCHED router.py → AENET-first routing")
