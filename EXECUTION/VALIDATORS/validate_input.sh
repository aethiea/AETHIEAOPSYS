#!/bin/bash

INPUT_FILE="$1"
LOG="$AETHIEA/LOGS/SYSTEM/pipeline.log"

if grep -q "^INPUT:" "$INPUT_FILE"; then
    echo "[VALIDATION_PASS] $(cat $INPUT_FILE)" >> "$LOG"
else
    echo "[VALIDATION_REJECT] $(cat $INPUT_FILE)" >> "$LOG"
fi
