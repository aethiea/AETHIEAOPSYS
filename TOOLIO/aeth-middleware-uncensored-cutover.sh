#!/usr/bin/env bash
set -Eeuo pipefail

MODE="${1:---plan}"
ROOT=/opt/AETHIEAOPSYS
SERVICE=aeth-middleware-awareness.service
SERVER="$ROOT/WORKSPACE/codex/middleware-awareness-aevps/runtime/llama.cpp/build-aevps/bin/llama-server"
PORT=3926

MODEL_REPO="arzaan789/mistral-7b-uncensored"
MODEL_ARTIFACT="mistral_7b_uncensored.Q4_K_M.gguf"
MODEL_DIR="$ROOT/DATA/AEVPS/MODELS/mistral-7b-v03-uncensored"
MODEL="$MODEL_DIR/$MODEL_ARTIFACT"
MODEL_URL="https://huggingface.co/${MODEL_REPO}/resolve/main/${MODEL_ARTIFACT}?download=true"
MODEL_API="https://huggingface.co/api/models/${MODEL_REPO}?blobs=true"

LAUNCHER=/usr/local/bin/aeth-middleware-awareness-uncensored
DROPIN_DIR=/etc/systemd/system/aeth-middleware-awareness.service.d
UNCENSORED_DROPIN="$DROPIN_DIR/99-uncensored.conf"
PREVIOUS_DROPIN="$DROPIN_DIR/99-abliterated.conf"
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
AETHER MIDDLEWARE // UNCENSORED MISTRAL CUTOVER PLAN
MODEL_REPOSITORY=$MODEL_REPO
MODEL_ARTIFACT=$MODEL_ARTIFACT
MODEL_DESTINATION=$MODEL
SHA256_SOURCE=HUGGINGFACE_MODEL_API_AT_APPLY_TIME
SERVICE=$SERVICE
LISTENER=127.0.0.1:$PORT
CONTEXT=8192
PARALLEL=1
THREADS=2
MEMORY_MAX=6G
PREVIOUS_CHECKPOINT_DROPIN=$PREVIOUS_DROPIN
NEW_CHECKPOINT_DROPIN=$UNCENSORED_DROPIN
AETHER_PROMPTS_CHANGED=NO
AETHER_BODY_CHANGED=NO
CREATOR_EXECUTOR_CHANGED=NO
AEMCP_CHANGED=NO
VRAG_CHANGED=NO
B43_CHANGED=NO
SYSTEMD_HARDENING_CHANGED=NO
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

resolve_upstream_sha256() {
    local metadata="$BACKUP/model-api.json"
    curl -fsSL --retry 3 --retry-delay 2 "$MODEL_API" -o "$metadata"
    python3 - "$metadata" "$MODEL_ARTIFACT" <<'PY'
import json
import pathlib
import sys

metadata = pathlib.Path(sys.argv[1])
artifact = sys.argv[2]
data = json.loads(metadata.read_text(encoding="utf-8"))
for item in data.get("siblings", []):
    if item.get("rfilename") != artifact:
        continue
    lfs = item.get("lfs") or {}
    sha = lfs.get("sha256")
    if isinstance(sha, str) and len(sha) == 64:
        print(sha.lower())
        raise SystemExit(0)
    raise SystemExit("artifact found but Hugging Face API did not expose lfs.sha256")
raise SystemExit("artifact not found in Hugging Face model metadata")
PY
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

restore_previous() {
    echo "ROLLBACK=START"
    rm -f "$UNCENSORED_DROPIN"
    systemctl daemon-reload
    systemctl restart "$SERVICE" || true
    if wait_health; then
        echo "ROLLBACK=PREVIOUS_CHECKPOINT_RESTORED"
    else
        echo "ROLLBACK=PREVIOUS_CHECKPOINT_HEALTH_FAILED" >&2
        return 1
    fi
}

apply() {
    require_root
    require_host
    [[ -x "$SERVER" ]] || { echo "STOP=LLAMA_SERVER_MISSING:$SERVER"; exit 3; }
    command -v curl >/dev/null || { echo "STOP=CURL_MISSING"; exit 3; }
    command -v python3 >/dev/null || { echo "STOP=PYTHON3_MISSING"; exit 3; }

    mkdir -p "$MODEL_DIR" "$DROPIN_DIR" "$BACKUP"

    echo "=== CURRENT SERVICE ==="
    systemctl show "$SERVICE" -p ActiveState -p SubState -p MainPID -p MemoryCurrent -p MemoryMax || true
    systemctl cat --no-pager "$SERVICE" >"$BACKUP/service-before.txt" || true
    [[ -f "$PREVIOUS_DROPIN" ]] && cp -a "$PREVIOUS_DROPIN" "$BACKUP/99-abliterated.conf"
    [[ -f "$UNCENSORED_DROPIN" ]] && cp -a "$UNCENSORED_DROPIN" "$BACKUP/99-uncensored.conf"

    echo "=== RESOLVE UPSTREAM SHA256 ==="
    EXPECTED_SHA="$(resolve_upstream_sha256)"
    echo "EXPECTED_SHA256=$EXPECTED_SHA"

    echo "=== MODEL ==="
    if [[ ! -s "$MODEL" ]]; then
        TMP="$MODEL.part"
        curl -fL --retry 3 --retry-delay 2 --continue-at - "$MODEL_URL" -o "$TMP"
        mv "$TMP" "$MODEL"
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

    cat >"$UNCENSORED_DROPIN" <<EOF
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
    echo "MIDDLEWARE_MODEL=MISTRAL_7B_V03_UNCENSORED_Q4_K_M"
    echo "CHECKPOINT_REPOSITORY=$MODEL_REPO"
    echo "CHECKPOINT_ARTIFACT=$MODEL_ARTIFACT"
    echo "MIDDLEWARE_3926=ONLINE"
    echo "MEMORY_HEADROOM_GUARD=PASS"
    echo "CHAT_TEMPLATE_RENDER=PASS"
    echo "CHAT_TEMPLATE_INJECTED_SYSTEM_TEXT=NO"
    echo "AETHER_PROMPTS_CHANGED=NO"
    echo "CREATOR_EXECUTOR_CHANGED=NO"
    echo "SYSTEMD_HARDENING_CHANGED=NO"
    echo "PREVIOUS_CHECKPOINT_ROLLBACK=READY"
    echo "BACKUP_ROOT=$BACKUP"
}

rollback() {
    require_root
    require_host
    restore_previous
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
