#!/usr/bin/env python3
import os
from pathlib import Path

TARGET = Path(os.environ["AETHIEA"]) / "CORE" / "router.py"

src = TARGET.read_text()

# Inject ROOT definition only if missing near AENET block
if 'AENET = ROOT / "LAYERS" / "AENET"' in src and 'ROOT =' not in src:
    fix = 'from pathlib import Path\nimport os\nROOT = Path(os.environ.get("AETHIEA", Path.cwd()))\n\n'
    src = fix + src

TARGET.write_text(src)
print("PATCHED → ROOT defined for router")
