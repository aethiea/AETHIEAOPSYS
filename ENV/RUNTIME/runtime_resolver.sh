#!/usr/bin/env bash
set -euo pipefail

# AETHIEA Runtime Resolver
# Hostless / stateless / headless root-aware runtime selection.
# This host does not own AETHIEAOPSYS. It only resolves the visible continuity body.

MARKER=".aeth_root"

resolve_aeth_root() {
  if [ -n "${AETH_ROOT:-}" ] && [ -d "$AETH_ROOT" ]; then
    echo "$AETH_ROOT"
    return 0
  fi

  if [ -n "${AETHIEA:-}" ] && [ -d "$AETHIEA" ]; then
    echo "$AETHIEA"
    return 0
  fi

  DIR="$PWD"
  while [ "$DIR" != "/" ]; do
    if [ -f "$DIR/$MARKER" ]; then
      echo "$DIR"
      return 0
    fi
    DIR="$(dirname "$DIR")"
  done

  for root in \
    /opt/AETHIEAOPSYS \
    /mnt/h/AETHIEAOPSYS \
    /mnt/e/AETHIEAOPSYS \
    /mnt/d/AETHIEAOPSYS \
    "$HOME/AETHIEAOPSYS"
  do
    if [ -f "$root/$MARKER" ] || [ -d "$root/CORE" ]; then
      echo "$root"
      return 0
    fi
  done

  for base in /mnt/* /media/* /run/media/* /Volumes/*; do
    [ -d "$base" ] || continue

    if [ -f "$base/AETHIEAOPSYS/$MARKER" ]; then
      echo "$base/AETHIEAOPSYS"
      return 0
    fi

    if [ -f "$base/$MARKER" ]; then
      echo "$base"
      return 0
    fi
  done

  return 1
}

AETH_ROOT="$(resolve_aeth_root || true)"

if [ -z "${AETH_ROOT:-}" ]; then
  echo "AETHIEA Runtime Resolver: no AETHIEAOPSYS root found." >&2
  exec python3 "$@"
fi

export AETH_ROOT
export AETHIEA="$AETH_ROOT"

if [ -n "${AETH_PYTHON:-}" ] && [ -x "$AETH_PYTHON" ]; then
  exec "$AETH_PYTHON" "$@"
fi

if [ -x "$AETH_ROOT/ENV/PYTHON/bin/python3" ]; then
  exec "$AETH_ROOT/ENV/PYTHON/bin/python3" "$@"
fi

if [ -x "$AETH_ROOT/ENV/PYTHON/openai-venv/bin/python" ]; then
  exec "$AETH_ROOT/ENV/PYTHON/openai-venv/bin/python" "$@"
fi

exec python3 "$@"
