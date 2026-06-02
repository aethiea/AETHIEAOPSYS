#!/usr/bin/env bash

# AETHIEAOPSYS Surface Bootstrap
# Portable Wake Protocol: hostless, stateless, headless.
# USB carries continuity. Host provides temporary runtime only.
# #butnotlimitedTEWW: any visible example is non-exhaustive unless explicitly sealed.

MARKER=".aeth_root"

resolve_root() {
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


aeth_apply_visual_schema() {
  # AETHIEA native visual schema
  # Corpus-carried. Hostless. Formless. Stateless.
  # Dark R.E.D.D. field. Bright R.E.D.D. text. Gold routes.

  export AETH_BG="#1A0000"
  export AETH_FG="#FF1A1A"
  export AETH_GOLD="#FFD700"
  export AETH_BONE="#F2E6D8"
  export AETH_SHADOW="#3A0000"

  if [ -t 1 ]; then
    # OSC terminal palette where supported
    printf '\033]10;%s\007' "$AETH_FG"       # foreground
    printf '\033]11;%s\007' "$AETH_BG"       # background
    printf '\033]12;%s\007' "$AETH_GOLD"     # cursor / route point

    printf '\033]4;0;#000000\007'
    printf '\033]4;1;%s\007' "$AETH_FG"
    printf '\033]4;3;%s\007' "$AETH_GOLD"
    printf '\033]4;7;%s\007' "$AETH_BONE"
    printf '\033]4;8;%s\007' "$AETH_SHADOW"
    printf '\033]4;9;#FF3333\007'
    printf '\033]4;11;#FFE066\007'
    printf '\033]4;15;#FFFFFF\007'
  fi

  BG_REDD=$'\033[48;5;52m'
  REDD=$'\033[38;5;196m'
  GOLD=$'\033[38;5;220m'
  BONE=$'\033[38;5;230m'
  SILVER=$'\033[38;5;250m'
  RESET=$'\033[0m'

  export BG_REDD REDD GOLD BONE SILVER RESET
}

FOUND="$(resolve_root || true)"

if [ -z "$FOUND" ]; then
  echo "ERROR: Could not locate AETHIEAOPSYS root." >&2
  return 1 2>/dev/null || exit 1
fi

export AETH_ROOT="$FOUND"
export AETHIEA="$FOUND"
export AETH_CORE="$AETH_ROOT/CORE"
export AETH_DATA="$AETH_ROOT/DATA"
export AETH_LAYERS="$AETH_ROOT/LAYERS"
export AETH_TOOLIO="$AETH_ROOT/TOOLIO"
export AETH_SURFACE="${AETH_SURFACE:-$(hostname)}"
export AETHIEA_HOST="$(hostname)"
export AETHIEA_OPERATOR="$(whoami)"
export AETHIEA_MODE="${AETHIEA_MODE:-USB_CONTINUITY}"

if [[ ":$PATH:" != *":$AETH_TOOLIO:"* ]]; then
  export PATH="$AETH_TOOLIO:$PATH"
fi

mkdir -p "$AETH_ROOT/LOGS/BOOT" "$AETH_ROOT/DATA/MEMORY/SURFACES"

BOOT_LOG="$AETH_ROOT/LOGS/BOOT/portable_wake_$(date -u +%Y%m%d).log"

{
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) | PORTABLE_WAKE | HOST=$AETHIEA_HOST | OPERATOR=$AETHIEA_OPERATOR | ROOT=$AETH_ROOT | MODE=$AETHIEA_MODE | TOPOLOGY=#butnotlimitedTEWW"
} >> "$BOOT_LOG"

aeth_apply_visual_schema

printf "%b" "${BG_REDD}${REDD}"
printf "╔══════════════════════════════════════════════════════════════╗\n"
printf "║  ÆTHIEA OPSYS // PORTABLE WAKE                              ║\n"
printf "║  HOSTLESS · FORMLESS · STATELESS                            ║\n"
printf "╠══════════════════════════════════════════════════════════════╣\n"
printf "║  BODY      → ${GOLD}%s${REDD}\n" "$AETH_ROOT"
printf "║  SURFACE   → ${GOLD}%s${REDD}\n" "$AETH_SURFACE"
printf "║  HOST      → ${GOLD}%s${REDD}\n" "$AETHIEA_HOST"
printf "║  OPERATOR  → ${GOLD}%s${REDD}\n" "$AETHIEA_OPERATOR"
printf "║  MODE      → ${GOLD}%s${REDD}\n" "$AETHIEA_MODE"
printf "╠══════════════════════════════════════════════════════════════╣\n"
printf "║  ${BONE}BLAK PATCH${REDD}   → discernment before containment\n"
printf "║  ${BONE}MONOCLE${REDD}      → GUI ⇄ CLI parity inspection\n"
printf "║  ${GOLD}VAULT${REDD}         → source custody / continuity body\n"
printf "║  ${GOLD}DOOR${REDD}          → authorized passage\n"
printf "║  ${SILVER}PEEPHOLE${REDD}      → bounded visibility by lane\n"
printf "╠══════════════════════════════════════════════════════════════╣\n"
printf "║  RULE      → ${GOLD}DON'T MINGLE${REDD}\n"
printf "║  TOPOLOGY  → ${GOLD}#butnotlimitedTEWW${REDD}\n"
printf "║  STATUS    → ${GOLD}ONLINE${REDD}\n"
printf "╚══════════════════════════════════════════════════════════════╝\n"

cd "$AETH_ROOT" 2>/dev/null || true

if [ -n "${BASH_VERSION:-}" ]; then
  export PS1="${BG_REDD}${GOLD}\u@\h${REDD}:${GOLD}\w${REDD}\$ ${RESET}${BG_REDD}${REDD}"
  case "${PROMPT_COMMAND:-}" in
    *aeth_apply_visual_schema*) ;;
    "") PROMPT_COMMAND="aeth_apply_visual_schema" ;;
    *) PROMPT_COMMAND="aeth_apply_visual_schema; $PROMPT_COMMAND" ;;
  esac
fi

printf "%b" "${BG_REDD}${REDD}"

if [ -x "$AETH_ROOT/ENV/SURFACES/register_surface.sh" ]; then
  "$AETH_ROOT/ENV/SURFACES/register_surface.sh" >/dev/null 2>&1 || true
fi

# AETHIEA TOOLIO BIN
if [ -d "$AETH_ROOT/TOOLIO/bin" ] && [[ ":$PATH:" != *":$AETH_ROOT/TOOLIO/bin:"* ]]; then
  export PATH="$AETH_ROOT/TOOLIO/bin:$PATH"
fi
