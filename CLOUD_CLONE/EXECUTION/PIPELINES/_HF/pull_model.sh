#!/bin/bash
set -euo pipefail
AETH_ROOT="${AETH_ROOT:-/mnt/e/AETHIEAOPSYS}"
MODEL_ID="$1"
SAFE_ID="${MODEL_ID//\//__}"
DOWNLOAD_DIR="$AETH_ROOT/MODELS/huggingface/downloads/$SAFE_ID"
mkdir -p "$DOWNLOAD_DIR"
huggingface-cli download "$MODEL_ID" --local-dir "$DOWNLOAD_DIR"
echo "$MODEL_ID" >> "$AETH_ROOT/MODELS/huggingface/manifests/downloaded.txt"
echo "Downloaded $MODEL_ID as $SAFE_ID"
