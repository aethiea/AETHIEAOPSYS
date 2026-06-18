#!/usr/bin/env bash
# AETHIEA ENVIRONMENT BOOT — CANONICAL
# Owner: dynamic environment exports.
# Does not own visible banner/header.
# Does not hardcode USB drive letters.
#
# .bashrc locates.
# aethiea_env.sh exports.
# ENV/SURFACES/bootstrap.sh displays.
# Host executes. AEUSB carries. Host does not own.

_aeth_env_valid_root() {
  local r="$1"
  [ -n "$r" ] || return 1
  [ -d "$r" ] || return 1
  [ -f "$r/.aeth_root" ] || return 1
  [ -f "$r/STATUS.md" ] || return 1
  [ ! -f "$r/AE320GB_HEAVY_BODY" ] || return 1
  [ ! -f "$r/.aeth_heavy_body" ] || return 1
}

_aeth_env_resolve_root() {
  local r d

  if declare -F aeth_root >/dev/null 2>&1; then
    r="$(aeth_root 2>/dev/null || true)"
    if _aeth_env_valid_root "$r"; then
      printf '%s\n' "$r"
      return 0
    fi
  fi

  for r in "${AETH_ROOT:-}" "${AETHIEA:-}" "${AETHIEAOPSYS:-}" "${AEUSB:-}"; do
    if _aeth_env_valid_root "$r"; then
      printf '%s\n' "$r"
      return 0
    fi
  done

  d="$PWD"
  while [ "$d" != "/" ]; do
    if _aeth_env_valid_root "$d"; then
      printf '%s\n' "$d"
      return 0
    fi
    d="$(dirname "$d")"
  done

  for r in /mnt/[a-z]/AETHIEAOPSYS /media/*/AETHIEAOPSYS /run/media/*/AETHIEAOPSYS /Volumes/*/AETHIEAOPSYS "$HOME/AETHIEAOPSYS" /opt/AETHIEAOPSYS; do
    if _aeth_env_valid_root "$r"; then
      printf '%s\n' "$r"
      return 0
    fi
  done

  return 1
}

FOUND="$(_aeth_env_resolve_root 2>/dev/null || true)"
if [ -z "$FOUND" ]; then
  return 0 2>/dev/null || exit 0
fi

export AETHIEA="$FOUND"
export AETH_ROOT="$FOUND"
export AETHIEA_ROOT="$FOUND"
export AETHIEAOPSYS="$FOUND"
export AEUSB="$FOUND"

export AETH_MODE="${AETH_MODE:-AEUSB_NATIVE}"
export AETHIEA_MODE="${AETHIEA_MODE:-USB_CONTINUITY}"
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
  [ -n "${1:-}" ] || return 0
  [ -d "$1" ] || return 0
  case ":$PATH:" in
    *":$1:"*) ;;
    *) export PATH="$1:$PATH" ;;
  esac
}

aeusb_prepend_path "$AETH_ROOT/TOOLIO/bin"
aeusb_prepend_path "$AETH_ROOT/TOOLIO"
aeusb_prepend_path "$AETH_ROOT/APT/bin"

if [ -f "$AETH_ROOT/TOOLIO/bin/aeusb-auth-env" ]; then
  . "$AETH_ROOT/TOOLIO/bin/aeusb-auth-env" || true
fi

export AETHIEA_ENV_LOADED_FOR="$AETH_ROOT"
