#!/usr/bin/env bash
# AETHIEAOPSYS Surface Bootstrap
# Canonical visible startup owner.
# Portable Wake Protocol: hostless, stateless, headless.
# USB carries continuity. Host provides temporary runtime only.
# #butnotlimitedTEWW: visible example does not close topology.

_aeth_boot_return_ok() {
  return 0 2>/dev/null || exit 0
}

_aeth_boot_valid_root() {
  local r="$1"
  [ -n "$r" ] || return 1
  [ -d "$r" ] || return 1
  [ -f "$r/.aeth_root" ] || return 1
  [ -f "$r/STATUS.md" ] || return 1
  [ ! -f "$r/AE320GB_HEAVY_BODY" ] || return 1
  [ ! -f "$r/.aeth_heavy_body" ] || return 1
}

resolve_root() {
  local r d

  if declare -F aeth_root >/dev/null 2>&1; then
    r="$(aeth_root 2>/dev/null || true)"
    if _aeth_boot_valid_root "$r"; then
      printf '%s\n' "$r"
      return 0
    fi
  fi

  for r in "${AETH_ROOT:-}" "${AETHIEA:-}" "${AETHIEAOPSYS:-}" "${AEUSB:-}"; do
    if _aeth_boot_valid_root "$r"; then
      printf '%s\n' "$r"
      return 0
    fi
  done

  d="$PWD"
  while [ "$d" != "/" ]; do
    if _aeth_boot_valid_root "$d"; then
      printf '%s\n' "$d"
      return 0
    fi
    d="$(dirname "$d")"
  done

  for r in /mnt/[a-z]/AETHIEAOPSYS /media/*/AETHIEAOPSYS /run/media/*/AETHIEAOPSYS /Volumes/*/AETHIEAOPSYS "$HOME/AETHIEAOPSYS" /opt/AETHIEAOPSYS; do
    if _aeth_boot_valid_root "$r"; then
      printf '%s\n' "$r"
      return 0
    fi
  done

  return 1
}

aeth_apply_visual_schema() {
  export AETH_BG="#1A0000"
  export AETH_FG="#FF1A1A"
  export AETH_GOLD="#FFD700"
  export AETH_BONE="#F2E6D8"
  export AETH_SHADOW="#3A0000"

  if [ -t 1 ]; then
    printf '\033]10;%s\007' "$AETH_FG"
    printf '\033]11;%s\007' "$AETH_BG"
    printf '\033]12;%s\007' "$AETH_GOLD"
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

  P_BG_REDD='\[\033[48;5;52m\]'
  P_REDD='\[\033[38;5;196m\]'
  P_GOLD='\[\033[38;5;220m\]'
  P_BONE='\[\033[38;5;230m\]'
  P_RESET='\[\033[0m\]'

  export BG_REDD REDD GOLD BONE SILVER RESET
  export P_BG_REDD P_REDD P_GOLD P_BONE P_RESET
}

FOUND="$(resolve_root || true)"

if [ -z "$FOUND" ]; then
  echo "ERROR: Could not locate AETHIEAOPSYS authority root." >&2
  return 1 2>/dev/null || exit 1
fi

export AETH_ROOT="$FOUND"
export AETHIEA="$FOUND"
export AETHIEA_ROOT="$FOUND"
export AETHIEAOPSYS="$FOUND"
export AEUSB="$FOUND"

if [ -f "$AETH_ROOT/ENV/SHELL/aethiea_env.sh" ]; then
  . "$AETH_ROOT/ENV/SHELL/aethiea_env.sh" || true
fi

export AETH_CORE="$AETH_ROOT/CORE"
export AETH_DATA="$AETH_ROOT/DATA"
export AETH_LAYERS="$AETH_ROOT/LAYERS"
export AETH_TOOLIO="$AETH_ROOT/TOOLIO"
export AETH_SURFACE="${AETH_SURFACE:-$(hostname)}"
export AETHIEA_HOST="$(hostname)"
export AETHIEA_OPERATOR="$(whoami)"
export AETHIEA_MODE="${AETHIEA_MODE:-USB_CONTINUITY}"

aeth_find_aexhd_root() {
  local r base

  aeth_is_aexhd_root() {
    local x="$1"

    [ -d "$x" ] || return 1
    [ "$x" != "$AETH_ROOT" ] || return 1

    # AEXHD is hostless. Marker proves body. Mount path does not.
    [ -f "$x/.aexhd_root" ] && return 0
    [ -f "$x/.aeth_memory_body" ] && return 0
    [ -f "$x/.aeth_heavy_body" ] && return 0
    [ -f "$x/AE320GB_HEAVY_BODY" ] && return 0

    return 1
  }

  if [ -n "${AEXHD_ROOT:-}" ] && aeth_is_aexhd_root "$AEXHD_ROOT"; then
    printf '%s\n' "$AEXHD_ROOT"
    return 0
  fi

  for r in /mnt/[a-z]/AETHIEAOPSYS /media/*/AETHIEAOPSYS /run/media/*/AETHIEAOPSYS /Volumes/*/AETHIEAOPSYS "$HOME/AETHIEAOPSYS" /opt/AETHIEAOPSYS; do
    aeth_is_aexhd_root "$r" || continue
    printf '%s\n' "$r"
    return 0
  done

  for base in /mnt/[a-z] /media/* /run/media/* /Volumes/*; do
    [ -d "$base" ] || continue
    [ -d "$base/AETHIEAOPSYS" ] || continue
    aeth_is_aexhd_root "$base/AETHIEAOPSYS" || continue
    printf '%s\n' "$base/AETHIEAOPSYS"
    return 0
  done

  return 1
}

if AEXHD_FOUND="$(aeth_find_aexhd_root 2>/dev/null)"; then
  export AEXHD_ROOT="$AEXHD_FOUND"
  export AEXHD_STATUS="ONLINE"
else
  export AEXHD_ROOT="${AEXHD_ROOT:-not mounted}"
  export AEXHD_STATUS="OFFLINE"
fi

if [[ ":$PATH:" != *":$AETH_TOOLIO:"* ]]; then
  export PATH="$AETH_TOOLIO:$PATH"
fi

if [ -d "$AETH_ROOT/TOOLIO/bin" ] && [[ ":$PATH:" != *":$AETH_ROOT/TOOLIO/bin:"* ]]; then
  export PATH="$AETH_ROOT/TOOLIO/bin:$PATH"
fi

aeth_apply_visual_schema

if [ "${AETH_SURFACE_BOOTSTRAP_LOADED_FOR:-}" = "$AETH_ROOT" ] && [ -z "${AETH_FORCE_BOOTSTRAP:-}" ]; then
  _aeth_boot_return_ok
fi

export AETH_SURFACE_BOOTSTRAP_LOADED_FOR="$AETH_ROOT"

mkdir -p "$AETH_ROOT/LOGS/BOOT" "$AETH_ROOT/DATA/MEMORY/SURFACES"

BOOT_LOG="$AETH_ROOT/LOGS/BOOT/portable_wake_$(date -u +%Y%m%d).log"

{
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) | PORTABLE_WAKE | HOST=$AETHIEA_HOST | OPERATOR=$AETHIEA_OPERATOR | ROOT=$AETH_ROOT | MODE=$AETHIEA_MODE | TOPOLOGY=#butnotlimitedTEWW"
} >> "$BOOT_LOG"

printf "%b" "${BG_REDD}${REDD}"
printf "╔══════════════════════════════════════════════════════════════╗\n"
printf "║  ÆTHIEA OPSYS // PORTABLE WAKE                              ║\n"
printf "║  HOSTLESS · FORMLESS · STATELESS                            ║\n"
printf "╠══════════════════════════════════════════════════════════════╣\n"
printf "║  HOSTESS   → ${GOLD}%s${REDD}\n" "$AETH_ROOT"
printf "║  AEXHD     → ${GOLD}%s${REDD} · %s\n" "$AEXHD_ROOT" "$AEXHD_STATUS"
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
printf "%b" "${RESET}"

cd "$AETH_ROOT" 2>/dev/null || true

if [ -n "${BASH_VERSION:-}" ]; then
  export PS1="${P_BG_REDD}${P_GOLD}\u@\h ${P_REDD}${AETHIEA_MODE} ${P_GOLD}DNY-5U5 ${P_BONE}\w ${P_REDD}\$ ${P_RESET}"
  case "${PROMPT_COMMAND:-}" in
    *aeth_apply_visual_schema*) ;;
    "") PROMPT_COMMAND="aeth_apply_visual_schema" ;;
    *) PROMPT_COMMAND="aeth_apply_visual_schema; $PROMPT_COMMAND" ;;
  esac
fi

if [ -x "$AETH_ROOT/ENV/SURFACES/register_surface.sh" ]; then
  "$AETH_ROOT/ENV/SURFACES/register_surface.sh" >/dev/null 2>&1 || true
fi
