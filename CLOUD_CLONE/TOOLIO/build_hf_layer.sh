#!/usr/bin/env bash
set -euo pipefail

AETH_ROOT="${AETH_ROOT:-/mnt/e/AETHIEAOPSYS}"
HF_BASE="$AETH_ROOT/MODELS/huggingface"
PIPELINE_HF="$AETH_ROOT/EXECUTION/PIPELINES/_HF"

mkdir -p "$HF_BASE"/{cache,downloads,gguf,safetensors,manifests,licenses}
mkdir -p "$PIPELINE_HF"
echo "AETH_ROOT = $AETH_ROOT"
echo "Created HF depot under $HF_BASE"

cat <<'SCRIPT' > "$PIPELINE_HF/pull_model.sh"
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
SCRIPT
# chmod skipped on Windows mount:  "$PIPELINE_HF/pull_model.sh"

echo "HF layer built successfully."
