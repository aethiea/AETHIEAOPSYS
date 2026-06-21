#!/usr/bin/env bash
# BEGIN AETHIEA_MARKER_RESOLVE
_aeth_resolve_root() {
  local p="${AETHIEA_ROOT:-${AETH_ROOT:-${AETHIEA:-${AETHIEAOPSYS:-$(pwd -P)}}}}"
  if [ -n "$p" ] && [ -f "$p/.aeth_root" ]; then (cd "$p" && pwd -P); return; fi
  p="$(pwd -P)"
  while [ "$p" != "/" ] && [ ! -f "$p/.aeth_root" ]; do p="$(dirname "$p")"; done
  if [ -f "$p/.aeth_root" ]; then (cd "$p" && pwd -P); return; fi
  for p in /mnt/*/AETHIEAOPSYS "$HOME/AETHIEAOPSYS" /opt/AETHIEAOPSYS; do
    [ -f "$p/.aeth_root" ] && { (cd "$p" && pwd -P); return; }
  done
  return 1
}
AETHIEA_ROOT="$(_aeth_resolve_root)" || { echo "NO_AETH_ROOT_FOUND"; exit 1; }
export AETHIEA_ROOT AETH_ROOT="$AETHIEA_ROOT" AETHIEA="$AETHIEA_ROOT" AETHIEAOPSYS="$AETHIEA_ROOT"
# END AETHIEA_MARKER_RESOLVE

set -euo pipefail

AETH_ROOT="${AETH_ROOT:-$AETHIEA_ROOT}"
HF_BASE="$AETH_ROOT/MODELS/huggingface"
PIPELINE_HF="$AETH_ROOT/EXECUTION/PIPELINES/_HF"

mkdir -p "$HF_BASE"/{cache,downloads,gguf,safetensors,manifests,licenses}
mkdir -p "$PIPELINE_HF"
echo "AETH_ROOT = $AETH_ROOT"
echo "Created HF depot under $HF_BASE"

cat <<'SCRIPT' > "$PIPELINE_HF/pull_model.sh"
#!/bin/bash
set -euo pipefail
AETH_ROOT="${AETH_ROOT:-$AETHIEA_ROOT}"
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
