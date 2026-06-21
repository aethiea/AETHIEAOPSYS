#!/bin/bash
set -euo pipefail
AETH_ROOT="${AETH_ROOT:-${AETHIEA:-}}"
if [ -z "$AETH_ROOT" ] || [ ! -f "$AETH_ROOT/.aeth_root" ]; then
  AETH_ROOT="$(pwd -P)"
  while [ "$AETH_ROOT" != "/" ] && [ ! -f "$AETH_ROOT/.aeth_root" ]; do
    AETH_ROOT="$(dirname "$AETH_ROOT")"
  done
fi
[ -f "$AETH_ROOT/.aeth_root" ] || { echo "NO_AETH_ROOT_FOUND"; exit 1; }
MODEL_ID="$1"
SAFE_ID="${MODEL_ID//\//__}"
DOWNLOAD_DIR="$AETH_ROOT/MODELS/huggingface/downloads/$SAFE_ID"
mkdir -p "$DOWNLOAD_DIR"
huggingface-cli download "$MODEL_ID" --local-dir "$DOWNLOAD_DIR"
echo "$MODEL_ID" >> "$AETH_ROOT/MODELS/huggingface/manifests/downloaded.txt"
echo "Downloaded $MODEL_ID as $SAFE_ID"
