#!/usr/bin/env bash
set -Eeuo pipefail

MODE="${1:---plan}"
ROOT=/opt/AETHIEAOPSYS
SERVICE=aeth-middleware-awareness.service
SERVER="$ROOT/WORKSPACE/codex/middleware-awareness-aevps/runtime/llama.cpp/build-aevps/bin/llama-server"
PORT=3926
MODEL_REPO="noctrex/Mistral-7B-Instruct-v0.3-abliterated-GGUF"
MODEL_ARTIFACT="Mistral-7B-Instruct-v0.3-abliterated-Q4_K_M.gguf"
MODEL_SHA256="71cc35de252f469bc28c9c216e1641a0be8b9a61da3f196a105f7c93091e787d"
MODEL_DIR="$ROOT/DATA/AEVPS/MODELS/mistral-7b-v03-abliterated"
MODEL="$MODEL_DIR/$MODEL_ARTIFACT"
MODEL_URL="https://huggingface.co/${MODEL_REPO}/resolve/main/${MODEL_ARTIFACT}?download=true"
LAUNCHER=/usr/local/bin/aeth-middleware-awareness-abliterated
DROPIN_DIR=/etc/systemd/system/aeth-middleware-awareness.service.d
ABLIT_DROPIN="$DROPIN_DIR/99-abliterated.conf"
DOLPHIN_DROPIN="$DROPIN_DIR/99-dolphin.conf"
DOLPHIN_DISABLED="$DROPIN_DIR/99-dolphin.conf.disabled"
STATE="$ROOT/STATE/aetherbot/middleware-model"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$STATE/$STAMP"
REQUIRED_MEMORY_MAX_BYTES=6442450944

require_root() {
    [[ "$(id -u)" -eq 0 ]] || { echo "STOP=ROOT_REQUIRED"; exit 2; }
}

require_host() {
    [[ "$(hostname -s)" == "aethieaopsys" ]] || { echo "STOP=RUN_FROM_AEVPS"; exit 2; }
}

show_plan() {
    cat <<EOF
AETHER MIDDLEWARE // ABLITERATED MISTRAL CUTOVER PLAN
MODEL_REPOSITORY=$MODEL_REPO
MODEL_ARTIFACT=$MODEL_ARTIFACT
MODEL_DESTINATION=$MODEL
EXPECTED_SHA256=$MODEL_SHA256
SERVICE=$SERVICE
LISTENER=127.0.0.1:$PORT
CONTEXT=8192
PARALLEL=1
THREADS=2
MEMORY_MAX=6G
DOLPHIN_DROPIN_TO_DISABLE=$DOLPHIN_DROPIN
ABLITERATED_DROPIN=$ABLIT_DROPIN
AETHER_BODY_CHANGED=NO
OPEN_IDENTITY_CHANGED=NO
AEMCP_CHANGED=NO
VRAG_CHANGED=NO
B43_CHANGED=NO
EXECUTION_BOUNDARY_CHANGED=NO
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

verify_memory_ceiling() {
    local value
    value="$(systemctl show "$SERVICE" -p MemoryMax --value)"
    if [[ "$value" == "infinity" ]]; then
        echo "MEMORY_MAX_EFFECTIVE=infinity"
        return 0
    fi
    if [[ ! "$value" =~ ^[0-9]+$ ]] || (( value < REQUIRED_MEMORY_MAX_BYTES )); then
        echo "STOP=MEMORY_MAX_NOT_6G_OR_HIGHER:$value" >&2
        return 1
    fi
    echo "MEMORY_MAX_EFFECTIVE=$value"
}

verify_chat_template() {
    local probe="$BACKUP/chat-template-probe.json"
    curl -fsS \
      -H 'Content-Type: application/json' \
      -d '{"messages":[{"role":"system","content":"AETHER_TEMPLATE_PROBE"},{"role":"user","content":"ping"}]}' \
      "http://127.0.0.1:${PORT}/apply-template" >"$probe"

    python3 - "$probe" <<'PY'
import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
data = json.loads(p.read_text(encoding="utf-8"))
prompt = data.get("prompt", "")
assert "AETHER_TEMPLATE_PROBE" in prompt, "system message missing from rendered template"
assert "ping" in prompt, "user message missing from rendered template"
for injected in (
    "You are Dolphin",
    "helpful AI assistant",
    "You are a helpful assistant",
):
    assert injected not in prompt, f"unexpected injected system text: {injected}"
print("CHAT_TEMPLATE_RENDER=PASS")
print("CHAT_TEMPLATE_INJECTED_SYSTEM_TEXT=NO")
PY
}

restore_dolphin() {
    echo "ROLLBACK=START"
    rm -f "$ABLIT_DROPIN"
    if [[ -f "$DOLPHIN_DISABLED" ]]; then
        mv -f "$DOLPHIN_DISABLED" "$DOLPHIN_DROPIN"
    fi
    systemctl daemon-reload
    systemctl restart "$SERVICE" || true
    echo "ROLLBACK=DOLPHIN_RESTORED"
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
    [[ -f "$DOLPHIN_DROPIN" ]] && cp -a "$DOLPHIN_DROPIN" "$BACKUP/99-dolphin.conf"
    [[ -f "$ABLIT_DROPIN" ]] && cp -a "$ABLIT_DROPIN" "$BACKUP/99-abliterated.conf"

    echo "=== MODEL ==="
    if [[ ! -s "$MODEL" ]]; then
        TMP="$MODEL.part"
        curl -fL --retry 3 --retry-delay 2 --continue-at - "$MODEL_URL" -o "$TMP"
        mv "$TMP" "$MODEL"
    fi

    ACTUAL_SHA="$(sha256sum "$MODEL" | awk '{print $1}')"
    echo "$ACTUAL_SHA  $MODEL"
    if [[ "$ACTUAL_SHA" != "$MODEL_SHA256" ]]; then
        echo "STOP=MODEL_SHA256_MISMATCH"
        echo "EXPECTED=$MODEL_SHA256"
        echo "ACTUAL=$ACTUAL_SHA"
        exit 4
    fi
    echo "MODEL_SHA256=PASS"

    chmod 0644 "$MODEL"
    chown d_ny5u5:aethieaops "$MODEL" || true
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

    # Disable the currently-active Dolphin override without deleting it.
    if [[ -f "$DOLPHIN_DROPIN" ]]; then
        mv -f "$DOLPHIN_DROPIN" "$DOLPHIN_DISABLED"
    fi

    cat >"$ABLIT_DROPIN" <<EOF
[Service]
ExecStart=
ExecStart=$LAUNCHER
MemoryMax=6G
EOF

    systemctl daemon-reload

    trap restore_dolphin ERR INT TERM
    systemctl restart "$SERVICE"
    wait_health
    verify_memory_ceiling
    verify_chat_template

    echo "=== ACTIVE MODEL ==="
    curl -fsS "http://127.0.0.1:${PORT}/v1/models" | tee "$BACKUP/models-after.json"
    echo
    grep -Fq "$MODEL" "$BACKUP/models-after.json"

    echo "=== SERVICE STATE ==="
    systemctl show "$SERVICE" -p ActiveState -p SubState -p MainPID -p MemoryCurrent -p MemoryMax
    ss -ltnp | grep "127.0.0.1:${PORT}" || true

    trap - ERR INT TERM
    echo "MIDDLEWARE_MODEL=MISTRAL_7B_INSTRUCT_V03_ABLITERATED_Q4_K_M"
    echo "MIDDLEWARE_ABLITERATED_MODEL=YES"
    echo "MIDDLEWARE_3926=ONLINE"
    echo "MEMORY_HEADROOM_GUARD=PASS"
    echo "CHAT_TEMPLATE_RENDER=PASS"
    echo "CHAT_TEMPLATE_INJECTED_SYSTEM_TEXT=NO"
    echo "AETHER_BODY_CHANGED=NO"
    echo "OPEN_IDENTITY_CHANGED=NO"
    echo "EXECUTION_BOUNDARY_CHANGED=NO"
    echo "DOLPHIN_ROLLBACK_FILE=$DOLPHIN_DISABLED"
    echo "BACKUP_ROOT=$BACKUP"
}

rollback() {
    require_root
    require_host
    restore_dolphin
    wait_health
    echo "ROLLBACK=DOLPHIN_ACTIVE"
}

case "$MODE" in
    --plan) show_plan ;;
    --apply) apply ;;
    --rollback) rollback ;;
    *)
        echo "usage: $0 [--plan|--apply|--rollback]" >&2
        exit 2
        ;;
esac
