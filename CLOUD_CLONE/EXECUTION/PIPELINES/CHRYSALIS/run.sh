#!/usr/bin/env bash
# BEGIN AETHIEA_MARKER_RESOLVE
_aeth_resolve_root() {
  local p="${AETHIEA_ROOT:-${AETH_ROOT:-${AETHIEA:-${AETHIEAOPSYS:-$(pwd -P)}}}}"
  if [ -n "$p" ] && [ -f "$p/.aeth_root" ]; then (cd "$p" && pwd -P); return; fi
  p="$(pwd -P)"
  while [ "$p" != "/" ] && [ ! -f "$p/.aeth_root" ]; do p="$(dirname "$p")"; done
  if [ -f "$p/.aeth_root" ]; then (cd "$p" && pwd -P); return; fi
  for p in /mnt/*/AETHIEAOPSYS "$HOME/AETHIEAOPSYS" /opt/AETHIEAOPSYS; do
    [ -f "$p/.aeth_root" ] && { (cd "$p" && pwd -P); return; }
  done
  return 1
}
AETHIEA_ROOT="$(_aeth_resolve_root)" || { echo "NO_AETH_ROOT_FOUND"; exit 1; }
export AETHIEA_ROOT AETH_ROOT="$AETHIEA_ROOT" AETHIEA="$AETHIEA_ROOT" AETHIEAOPSYS="$AETHIEA_ROOT"
# END AETHIEA_MARKER_RESOLVE

set -euo pipefail

ROOT="${AETHIEA:-$AETHIEA_ROOT}"
PIPE="$ROOT/EXECUTION/PIPELINES/CHRYSALIS"
CONFIG="$PIPE/CONFIG/pipeline.json"
SECURITY_LOG="$ROOT/EXECUTION/REPORTS/security.log"
STAMP="$(date -u +%Y-%m-%dT%H-%M-%SZ)"

mkdir -p "$PIPE/INPUT" "$PIPE/PROCESS" "$PIPE/OUTPUT"/{CONTENT,AUDIO,VIDEO,TEXT,DATA,GENERAL} "$PIPE/LOGS" "$PIPE/REJECTED" "$ROOT/EXECUTION/REPORTS"

echo "$STAMP | CHRYSALIS | START" >> "$PIPE/LOGS/pipeline.log"

for job in "$PIPE"/INPUT/*.json; do
  [ -e "$job" ] || continue
  name="$(basename "$job")"

  VALIDATION="$(jq -r --slurpfile cfg "$CONFIG" '
    . as $job |
    $cfg[0] as $cfg |
    if ([ $cfg.required_fields[] | select($job[.] == null) ] | length) > 0 then
      "missing_required_fields"
    elif (($cfg.allowed_types | index(($job.type // "general"))) | not) then
      "invalid_type"
    elif (($cfg.allowed_actions | index($job.action)) | not) then
      "action_not_allowed"
    elif (($job.status // "") != $cfg.required_status) then
      "invalid_status"
    else
      "ok"
    end
  ' "$job")"

  
  case "$VALIDATION" in
    missing_required_fields) SEVERITY="low" ;;
    invalid_status) SEVERITY="low" ;;
    invalid_type) SEVERITY="medium" ;;
    action_not_allowed) SEVERITY="medium" ;;
    private_execution_denied) SEVERITY="high" ;;
    *) SEVERITY="unknown" ;;
  esac

if [ "$VALIDATION" != "ok" ]; then
    echo "$STAMP | CHRYSALIS | REJECT | $name | $VALIDATION" >> "$PIPE/LOGS/pipeline.log"
    jq --arg stamp "$STAMP" --arg pipe "CHRYSALIS" --arg reason "$VALIDATION" --arg severity "$SEVERITY" \
      '.status="rejected" | .rejected_at=$stamp | .pipeline=$pipe | .reason=$reason | .severity=$severity' \
      "$job" > "$PIPE/REJECTED/${name%.json}.rejected.json"
    mv "$job" "$PIPE/PROCESS/${name%.json}.rejected.source.json"
    continue
  fi

  TYPE="$(jq -r '.type // "general"' "$job" | tr '[:lower:]' '[:upper:]')"

  case "$TYPE" in
    CONTENT) DEST="CONTENT" ;;
    AUDIO) DEST="AUDIO" ;;
    VIDEO) DEST="VIDEO" ;;
    TEXT) DEST="TEXT" ;;
    DATA) DEST="DATA" ;;
    *) DEST="GENERAL" ;;
  esac

  echo "$STAMP | CHRYSALIS | PROCESS | $name | TYPE=$TYPE | DEST=$DEST" >> "$PIPE/LOGS/pipeline.log"

  cp "$job" "$PIPE/PROCESS/$name"

  jq --arg stamp "$STAMP" --arg pipe "CHRYSALIS" --arg dest "$DEST" \
    '.status="processed" | .processed_at=$stamp | .pipeline=$pipe | .routed_to=$dest' \
    "$job" > "$PIPE/OUTPUT/$DEST/${name%.json}.processed.json"

  echo "$STAMP | CHRYSALIS | OUTPUT | $DEST/${name%.json}.processed.json" >> "$PIPE/LOGS/pipeline.log"

  mv "$job" "$PIPE/PROCESS/${name%.json}.done.json"
done

echo "$STAMP | CHRYSALIS | END" >> "$PIPE/LOGS/pipeline.log"
echo "CHRYSALIS PIPELINE EXECUTED"
