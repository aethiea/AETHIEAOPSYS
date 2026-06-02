#!/usr/bin/env bash
set -euo pipefail

AETHIEA_ROOT="${AETHIEA_ROOT:-/mnt/h/AETHIEAOPSYS}"
LOG_DIR="$AETHIEA_ROOT/LOGS/HERMES"
mkdir -p "$LOG_DIR"

echo "HERMES ONLINE"
echo "Root: $AETHIEA_ROOT"
echo "Mode: AEUSB_CARRIED"
echo "Role: courier / interface membrane"
echo "Doctrine: Host executes. AEUSB carries. Host does not own."
echo "Timestamp UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG_DIR/hermes_boot.log"
