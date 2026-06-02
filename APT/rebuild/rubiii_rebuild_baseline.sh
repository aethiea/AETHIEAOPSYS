#!/usr/bin/env bash
set -euo pipefail

AETHIEA_ROOT="${AETHIEA_ROOT:-/mnt/h/AETHIEAOPSYS}"
MANIFEST_DIR="$AETHIEA_ROOT/APT/manifests"
LOG_DIR="$AETHIEA_ROOT/LOGS/SYSTEM"

mkdir -p "$LOG_DIR"

echo "AETHIEA RUBIII REBUILD BASELINE"
echo "Root: $AETHIEA_ROOT"
echo "Doctrine: #butnotlimitedTEWW"
echo "This rebuild script restores a known baseline, not an exhaustive boundary."

sudo apt update

if ls "$MANIFEST_DIR"/rubiii_manual_packages_after_upgrade_*.txt >/dev/null 2>&1; then
  MANUAL_FILE="$(ls -t "$MANIFEST_DIR"/rubiii_manual_packages_after_upgrade_*.txt | head -n 1)"
elif ls "$MANIFEST_DIR"/rubiii_manual_packages_postupdate_*.txt >/dev/null 2>&1; then
  MANUAL_FILE="$(ls -t "$MANIFEST_DIR"/rubiii_manual_packages_postupdate_*.txt | head -n 1)"
else
  MANUAL_FILE="$(ls -t "$MANIFEST_DIR"/rubiii_manual_packages_*.txt | head -n 1)"
fi

echo "Using manual package baseline: $MANUAL_FILE"

xargs -r sudo apt install -y < "$MANUAL_FILE"

echo "Rebuild baseline complete."
echo "Confirmed here, not confined here."
