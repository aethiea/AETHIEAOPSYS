#!/usr/bin/env bash
set -euo pipefail

ROOT="${AETHIEA:-${AETH_ROOT:-/opt/AETHIEAOPSYS}}"

if [ ! -f "$ROOT/.aeth_root" ]; then
  if [ -f /opt/AETHIEAOPSYS/.aeth_root ]; then
    ROOT="/opt/AETHIEAOPSYS"
  elif [ -f /mnt/h/AETHIEAOPSYS/.aeth_root ]; then
    ROOT="/mnt/h/AETHIEAOPSYS"
  fi
fi

LOG="$ROOT/LOGS/SYSTEM/runtime.log"
mkdir -p "$(dirname "$LOG")"

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) START AETHIEAOPSYS ROOT=$ROOT HOST=$(hostname)" >> "$LOG"

PORTAL="$ROOT/DOMAINS/thematriculation.cc/aether/PORTAL"

if [ -d "$PORTAL" ]; then
  pkill -f "http.server 3000" 2>/dev/null || true
  cd "$PORTAL"
  nohup python3 -m http.server 3000 >> "$LOG" 2>&1 &
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) PORTAL RUNNING :3000" >> "$LOG"
else
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) PORTAL SKIPPED missing=$PORTAL" >> "$LOG"
fi

if [ -f "$ROOT/ENV/API/cloudflare_tunnel.env" ]; then
  # shellcheck disable=SC1090
  source "$ROOT/ENV/API/cloudflare_tunnel.env"

  if [ -n "${CLOUDFLARED_TUNNEL_TOKEN:-}" ]; then
    pkill -f "cloudflared tunnel run" 2>/dev/null || true
    nohup cloudflared tunnel run --token "$CLOUDFLARED_TUNNEL_TOKEN" >> "$LOG" 2>&1 &
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) CLOUDFLARED RUNNING" >> "$LOG"
  else
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) CLOUDFLARED SKIPPED token empty" >> "$LOG"
  fi
else
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) CLOUDFLARED SKIPPED no ENV/API/cloudflare_tunnel.env" >> "$LOG"
fi

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) AETHIEAOPSYS START COMPLETE" >> "$LOG"
echo "AETHIEA START COMPLETE → $ROOT"
