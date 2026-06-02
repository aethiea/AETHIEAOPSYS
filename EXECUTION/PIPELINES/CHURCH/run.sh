#!/usr/bin/env bash
set -euo pipefail

ROOT="${AETHIEA:-/mnt/h/AETHIEAOPSYS}"
PIPE="$ROOT/EXECUTION/PIPELINES/CHURCH"
CONFIG="$PIPE/CONFIG/pipeline.json"
SECURITY_LOG="$ROOT/EXECUTION/REPORTS/security.log"
STAMP="$(date -u +%Y-%m-%dT%H-%M-%SZ)"

mkdir -p "$PIPE/INPUT" "$PIPE/PROCESS" "$PIPE/OUTPUT"/{CONTENT,AUDIO,VIDEO,TEXT,DATA,GENERAL} "$PIPE/LOGS" "$PIPE/REJECTED" "$ROOT/EXECUTION/REPORTS"

echo "$STAMP | CHURCH | START" >> "$PIPE/LOGS/pipeline.log"

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
    echo "$STAMP | CHURCH | REJECT | $name | $VALIDATION" >> "$PIPE/LOGS/pipeline.log"
    jq --arg stamp "$STAMP" --arg pipe "CHURCH" --arg reason "$VALIDATION" --arg severity "$SEVERITY" \
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

  echo "$STAMP | CHURCH | PROCESS | $name | TYPE=$TYPE | DEST=$DEST" >> "$PIPE/LOGS/pipeline.log"

  cp "$job" "$PIPE/PROCESS/$name"

  jq --arg stamp "$STAMP" --arg pipe "CHURCH" --arg dest "$DEST" \
    '.status="processed" | .processed_at=$stamp | .pipeline=$pipe | .routed_to=$dest' \
    "$job" > "$PIPE/OUTPUT/$DEST/${name%.json}.processed.json"

  echo "$STAMP | CHURCH | OUTPUT | $DEST/${name%.json}.processed.json" >> "$PIPE/LOGS/pipeline.log"

  mv "$job" "$PIPE/PROCESS/${name%.json}.done.json"
done

echo "$STAMP | CHURCH | END" >> "$PIPE/LOGS/pipeline.log"
echo "CHURCH PIPELINE EXECUTED"
