#!/usr/bin/env bash
set -euo pipefail

AETHIEA="${AETHIEA:-/mnt/h/AETHIEAOPSYS}"

cd "$AETHIEA"
"$AETHIEA/TOOLIO/aeth_cloud_clone"
