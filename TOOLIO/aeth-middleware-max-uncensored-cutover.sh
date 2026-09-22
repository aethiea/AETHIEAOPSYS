#!/usr/bin/env bash
set -Eeuo pipefail

MODE="${1:---plan}"
ROOT=/opt/AETHIEAOPSYS
SERVICE=aeth-middleware-awareness.service
SERVER="$ROOT/WORKSPACE/codex/middleware-awareness-aevps/runtime/llama.cpp/build-aevps/bin/llama-server"
PORT=3926

MODEL_REPO="arzaan789/mistral-7b-uncensored"
MODEL_ARTIFACT="mistral_7b_uncensored.Q4_K_M.gguf"
MODEL_DIR="$ROOT/DATA/AEVPS/MODELS/mistral-7b-v03-max-uncensored"
MODEL="$MODEL_DIR/$MODEL_ARTIFACT"
MODEL_URL="https://huggingface.co/${MODEL_REPO}/resolve/main/${MODEL_ARTIFACT}?download=true"
MODEL_RAW_META="https://huggingface.co/${MODEL_REPO}/raw/main/${MODEL_ARTIFACT}"
MIN_MODEL_BYTES=4000000000

LAUNCHER=/usr/local/bin/aeth-middleware-awareness-max-uncensored
DROPIN_DIR=/etc/systemd/system/aeth-middleware-awareness.service.d
NEW_DROPIN="$DROPIN_DIR/99-max-uncensored.conf"
OLD_DROPIN="$DROPIN_DIR/99-abliterated.conf"
OLD_DISABLED="$DROPIN_DIR/99-abliterated.conf.disabled-by-max-uncensored"

STATE="$ROOT/STATE/aetherbot/middleware-model"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$STATE/$STAMP-max-uncensored"
REQUIRED_MEMORY_MAX_BYTES=6442450944

require_root() {
    [[ "$(id -u)" -eq 0 ]] || { echo "STOP=ROOT_REQUIRED"; exit 2; }
}

require_host() {
    [[ "$(hostname -s)" == "aethieaopsys" ]] || { echo "STOP=RUN_FROM_AEVPS"; exit 2; }
}

show_plan() {
    cat <<EOF
AETHER MIDDLEWARE // MAX-UNCENSORED CHECKPOINT CUTOVER PLAN
MODEL_REPOSITORY=$MODEL_REPO
MODEL_ARTIFACT=$MODEL_ARTIFACT
MODEL_DESTINATION=$MODEL
LISTENER=127.0.0.1:$PORT
CONTEXT=8192
PARALLEL=1
THREADS=2
MEMORY_MAX=6G
CURRENT_ABLITERATED_DROPIN=$OLD_DROPIN
NEW_DROPIN=$NEW_DROPIN
MIDDLEWARE_ONLY=YES
AETHER_BODY_CHANGED=NO
OPEN_SYSTEM_CHANGED=NO
CODE_ENGINE_CHANGED=NO
AEMCP_CHANGED=NO
VRAG_CHANGED=NO
B43_CHANGED=NO
TOOL_EXECUTOR_CHANGED=NO
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

upstream_sha256() {
    local pointer sha
    pointer="$(curl -fsSL "$MODEL_RAW_META")" || return 1
    sha="$(printf '%s\n' "$pointer" | sed -n 's/^oid sha256:\([0-9a-fA-F]\{64\}\)$/\1/p' | head -1)"
    [[ "$sha" =~ ^[0-9a-fA-F]{64}$ ]] || return 1
    printf '%s\n' "${sha,,}"
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
    "safety policy",
    "content policy",
):
    assert injected.lower() not in prompt.lower(), f"unexpected injected system text: {injected}"
print("CHAT_TEMPLATE_RENDER=PASS")
print("CHAT_TEMPLATE_INJECTED_SYSTEM_TEXT=NO")
PY
}

restore_previous() {
    echo "ROLLBACK=START"
    rm -f "$NEW_DROPIN"
    if [[ -f "$OLD_DISABLED" ]]; then
        mv -f "$OLD_DISABLED" "$OLD_DROPIN"
    fi
    systemctl daemon-reload
    systemctl restart "$SERVICE" || true
    echo "ROLLBACK=PREVIOUS_ABLITERATED_RESTORED"
}

apply() {
    require_root
    require_host
    [[ -x "$SERVER" ]] || { echo "STOP=LLAMA_SERVER_MISSING:$SERVER"; exit 3; }
    command -v curl >/dev/null || { echo "STOP=CURL_MISSING"; exit 3; }
    command -v sha256sum >/dev/null || { echo "STOP=SHA256SUM_MISSING"; exit 3; }

    mkdir -p "$MODEL_DIR" "$DROPIN_DIR" "$BACKUP"

    echo "=== CURRENT SERVICE ==="
    systemctl show "$SERVICE" -p ActiveState -p SubState -p MainPID -p MemoryCurrent -p MemoryMax || true
    systemctl cat "$SERVICE" >"$BACKUP/service-before.txt" || true
    [[ -f "$OLD_DROPIN" ]] && cp -a "$OLD_DROPIN" "$BACKUP/99-abliterated.conf"
    [[ -f "$NEW_DROPIN" ]] && cp -a "$NEW_DROPIN" "$BACKUP/99-max-uncensored.conf"

    echo "=== UPSTREAM MODEL IDENTITY ==="
    EXPECTED_SHA="$(upstream_sha256)" || {
        echo "STOP=UPSTREAM_SHA256_UNAVAILABLE"
        exit 4
    }
    echo "UPSTREAM_SHA256=$EXPECTED_SHA"

    echo "=== MODEL ==="
    if [[ ! -s "$MODEL" ]]; then
        TMP="$MODEL.part"
        curl -fL --retry 3 --retry-delay 2 --continue-at - "$MODEL_URL" -o "$TMP"
        mv "$TMP" "$MODEL"
    fi

    MODEL_BYTES="$(stat -c %s "$MODEL")"
    if (( MODEL_BYTES < MIN_MODEL_BYTES )); then
        echo "STOP=MODEL_TOO_SMALL:$MODEL_BYTES"
        exit 4
    fi

    ACTUAL_SHA="$(sha256sum "$MODEL" | awk '{print $1}')"
    echo "$ACTUAL_SHA  $MODEL"
    if [[ "$ACTUAL_SHA" != "$EXPECTED_SHA" ]]; then
        echo "STOP=MODEL_SHA256_MISMATCH"
        echo "EXPECTED=$EXPECTED_SHA"
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

    # Preserve the currently working abliterated configuration for rollback.
    if [[ -f "$OLD_DROPIN" ]]; then
        mv -f "$OLD_DROPIN" "$OLD_DISABLED"
    fi

    cat >"$NEW_DROPIN" <<EOF
[Service]
ExecStart=
ExecStart=$LAUNCHER
MemoryMax=6G
EOF

    systemctl daemon-reload

    trap restore_previous ERR INT TERM
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
    echo "MIDDLEWARE_MODEL=MISTRAL_7B_V03_MAX_UNCENSORED_Q4_K_M"
    echo "MIDDLEWARE_PUBLISHER_REPORTED_REFUSAL_TEST=0_OF_64_HARMFUL_AND_0_OF_64_HARMLESS"
    echo "MIDDLEWARE_3926=ONLINE"
    echo "MEMORY_HEADROOM_GUARD=PASS"
    echo "CHAT_TEMPLATE_RENDER=PASS"
    echo "CHAT_TEMPLATE_INJECTED_SYSTEM_TEXT=NO"
    echo "MIDDLEWARE_ONLY=YES"
    echo "AETHER_BODY_CHANGED=NO"
    echo "OPEN_SYSTEM_CHANGED=NO"
    echo "CODE_ENGINE_CHANGED=NO"
    echo "TOOL_EXECUTOR_CHANGED=NO"
    echo "PREVIOUS_MODEL_ROLLBACK_FILE=$OLD_DISABLED"
    echo "BACKUP_ROOT=$BACKUP"
}

rollback() {
    require_root
    require_host
    restore_previous
    wait_health
    echo "ROLLBACK=PREVIOUS_ABLITERATED_ACTIVE"
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
