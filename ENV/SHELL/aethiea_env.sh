#!/usr/bin/env bash

# USB-native contract: all mutable AETHIEA state resolves under this root.
export AETHIEA="/mnt/h/AETHIEAOPSYS"
export AETH_ROOT="$AETHIEA"
export AETHIEA_ROOT="$AETHIEA"
export AETHIEAOPSYS="$AETHIEA"
export AEUSB="$AETHIEA"
export AETH_MODE="${AETH_MODE:-AEUSB_NATIVE}"
export AETHIEA_MODE="${AETHIEA_MODE:-USB_NATIVE_ROUTED}"
export AETH_SURFACE="${AETH_SURFACE:-$(hostname)}"
export AETHIEA_SURFACE="${AETHIEA_SURFACE:-$AETH_SURFACE}"

export AETH_CORE="$AETH_ROOT/CORE"
export AETH_DATA="$AETH_ROOT/DATA"
export AETH_LAYERS="$AETH_ROOT/LAYERS"
export AETH_TOOLIO="$AETH_ROOT/TOOLIO"
export AETH_EXECUTION="$AETH_ROOT/EXECUTION"
export AETH_LOGS="$AETH_ROOT/LOGS"
export AETH_MODELS="$AETH_ROOT/MODELS"
export AETH_RUN="$AETH_ROOT/RUN"
export AETH_TEMP="$AETH_ROOT/TEMP"

export OLLAMA_MODELS="$AETH_ROOT/DATA/OLLAMA"
export HF_HOME="$AETH_ROOT/MODELS/huggingface/cache"
export HF_HUB_CACHE="$AETH_ROOT/MODELS/huggingface/cache/hub"
export TRANSFORMERS_CACHE="$AETH_ROOT/MODELS/huggingface/cache/transformers"
export HF_DATASETS_CACHE="$AETH_ROOT/MODELS/huggingface/cache/datasets"
export PIP_CACHE_DIR="$AETH_ROOT/ENV/PYTHON/pip-cache"
export PYTHONPYCACHEPREFIX="$AETH_ROOT/ENV/PYTHON/pycache"
export NPM_CONFIG_CACHE="$AETH_ROOT/ENV/RUNTIME/npm-cache"
export WRANGLER_HOME="$AETH_ROOT/.wrangler"

aeusb_prepend_path() {
  case ":$PATH:" in
    *":$1:"*) ;;
    *) export PATH="$1:$PATH" ;;
  esac
}

aeusb_prepend_path "$AETH_ROOT/TOOLIO/bin"
aeusb_prepend_path "$AETH_ROOT/TOOLIO"
aeusb_prepend_path "$AETH_ROOT/APT/bin"
