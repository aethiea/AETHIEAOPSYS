#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

ROOT = Path(os.environ["AETHIEA"])
AENET = ROOT / "LAYERS" / "AENET"
CF = AENET / "CLOUDFLARE"
OLD = ROOT / "Cloudflare"
CORE = ROOT / "CORE" / "aeth.py"

CF.mkdir(parents=True, exist_ok=True)

if OLD.exists() and OLD.is_dir():
    for item in OLD.iterdir():
        dest = CF / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)
    shutil.rmtree(OLD)

(AENET / "README.md").write_text(
    "CLOUDFLARE -> edge ingress/egress\n"
    "TUNNELS -> routing\n"
    "AUTH -> identity\n"
)

text = CORE.read_text()
marker = "# --- AENET ROUTES ---"
head = text.split(marker)[0].rstrip()

block = '''
# --- AENET ROUTES ---
AENET = ROOT / "LAYERS" / "AENET"
routes.update({
    "aenet": AENET,
    "cloudflare": AENET / "CLOUDFLARE",
})
'''

CORE.write_text(head + "\n\n" + block)
print("PATCH OK -> AENET/CLOUDFLARE idempotent")
