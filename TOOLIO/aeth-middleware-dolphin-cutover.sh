#!/usr/bin/env bash
set -Eeuo pipefail

MODE="${1:---plan}"
ROOT=/opt/AETHIEAOPSYS
SERVICE=aeth-middleware-awareness.service
SERVER="$ROOT/WORKSPACE/codex/middleware-awareness-aevps/runtime/llama.cpp/build-aevps/bin/llama-server"
PORT=3926
MODEL_REPO="${MODEL_REPO:-lmstudio-community/dolphin-2.8-mistral-7b-v02-GGUF}"
MODEL_ARTIFACT="${MODEL_ARTIFACT:-dolphin-2.8-mistral-7b-v02.Q4_K_M.gguf}"
MODEL_DIR="$ROOT/DATA/AEVPS/MODELS/dolphin-2.8-mistral-7b-v02"
MODEL="$MODEL_DIR/$MODEL_ARTIFACT"
MODEL_URL="https://huggingface.co/${MODEL_REPO}/resolve/main/${MODEL_ARTIFACT}?download=true"
LAUNCHER=/usr/local/bin/aeth-middleware-awareness-dolphin
DROPIN_DIR=/etc/systemd/system/aeth-middleware-awareness.service.d
DROPIN="$DROPIN_DIR/30-dolphin.conf"
STATE="$ROOT/STATE/aetherbot/middleware-model"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$STATE/$STAMP"

require_root() {
    [[ "$(id -u)" -eq 0 ]] || { echo "STOP=ROOT_REQUIRED"; exit 2; }
}

require_host() {
    [[ "$(hostname -s)" == "aethieaopsys" ]] || { echo "STOP=RUN_FROM_AEVPS"; exit 2; }
}

show_plan() {
    cat <<EOF
AETHER MIDDLEWARE // DOLPHIN CUTOVER PLAN
MODEL_REPOSITORY=$MODEL_REPO
MODEL_ARTIFACT=$MODEL_ARTIFACT
MODEL_DESTINATION=$MODEL
SERVICE=$SERVICE
LISTENER=127.0.0.1:$PORT
CONTEXT=8192
PARALLEL=1
THREADS=2
MEMORY_MAX=6G
CURRENT_MISTRAL_DROPIN_PRESERVED=$DROPIN_DIR/20-mistral.conf
DOLPHIN_DROPIN=$DROPIN
ROLLBACK=remove 30-dolphin.conf and restart service
AETHER_BODY_CHANGED=NO
AEMCP_CHANGED=NO
B43_CHANGED=NO
VRAG_CHANGED=NO
EOF
}

wait_health() {
    local i
    for i in $(seq 1 120); do
        if curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    return 1
}

rollback() {
    echo "ROLLBACK=START"
    rm -f "$DROPIN"
    systemctl daemon-reload
    systemctl restart "$SERVICE" || true
    echo "ROLLBACK=20_MISTRAL_RESTORED"
}

apply() {
    require_root
    require_host

    [[ -x "$SERVER" ]] || { echo "STOP=LLAMA_SERVER_MISSING:$SERVER"; exit 3; }
    command -v curl >/dev/null || { echo "STOP=CURL_MISSING"; exit 3; }

    mkdir -p "$MODEL_DIR" "$DROPIN_DIR" "$BACKUP"

    echo "=== CURRENT SERVICE ==="
    systemctl show "$SERVICE" -p ActiveState -p SubState -p MainPID -p MemoryCurrent -p MemoryMax || true
    systemctl cat "$SERVICE" >"$BACKUP/service-before.txt" || true
    [[ -f "$DROPIN_DIR/20-mistral.conf" ]] && cp -a "$DROPIN_DIR/20-mistral.conf" "$BACKUP/20-mistral.conf"

    echo "=== MODEL ==="
    if [[ ! -s "$MODEL" ]]; then
        TMP="$MODEL.part"
        curl -fL --retry 3 --retry-delay 2 --continue-at - "$MODEL_URL" -o "$TMP"
        mv "$TMP" "$MODEL"
    fi
    chmod 0644 "$MODEL"
    chown d_ny5u5:aethieaops "$MODEL" || true
    sha256sum "$MODEL" | tee "$BACKUP/model.sha256"
    runuser -u d_ny5u5 -- test -r "$MODEL" || { echo "STOP=MODEL_NOT_READABLE_BY_SERVICE_USER"; exit 4; }

    cat >"$LAUNCHER" <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail
exec "$SERVER" \\
  --model "$MODEL" \\
  --host 127.0.0.1 \\
  --port $PORT \\
  --ctx-size 8192 \\
  --parallel 1 \\
  --threads 2 \\
  --jinja \\
  --no-webui \\
  --batch-size 128 \\
  --ubatch-size 32 \\
  --cache-type-k q4_0 \\
  --cache-type-v q4_0 \\
  --flash-attn on
EOF
    chmod 0755 "$LAUNCHER"

    cat >"$DROPIN" <<EOF
[Service]
ExecStart=
ExecStart=$LAUNCHER
MemoryMax=6G
EOF

    systemctl daemon-reload

    trap rollback ERR INT TERM
    systemctl restart "$SERVICE"
    wait_health

    echo "=== ACTIVE MODEL ==="
    curl -fsS "http://127.0.0.1:${PORT}/v1/models" | tee "$BACKUP/models-after.json"
    echo
    grep -Fq "$MODEL" "$BACKUP/models-after.json"

    echo "=== SERVICE STATE ==="
    systemctl show "$SERVICE" -p ActiveState -p SubState -p MainPID -p MemoryCurrent -p MemoryMax
    ss -ltnp | grep "127.0.0.1:${PORT}" || true

    trap - ERR INT TERM
    echo "MIDDLEWARE_MODEL=DOLPHIN_2.8_MISTRAL_7B_V02_Q4_K_M"
    echo "MIDDLEWARE_UNCENSORED_MODEL=YES"
    echo "MIDDLEWARE_3926=ONLINE"
    echo "AETHER_BODY_CHANGED=NO"
    echo "B43_CHANGED=NO"
    echo "ROLLBACK_DROPIN=$DROPIN"
    echo "BACKUP_ROOT=$BACKUP"
}

case "$MODE" in
    --plan)
        show_plan
        ;;
    --apply)
        apply
        ;;
    --rollback)
        require_root
        require_host
        rm -f "$DROPIN"
        systemctl daemon-reload
        systemctl restart "$SERVICE"
        wait_health
        echo "ROLLBACK=20_MISTRAL_ACTIVE"
        ;;
    *)
        echo "usage: $0 [--plan|--apply|--rollback]" >&2
        exit 2
        ;;
esac
