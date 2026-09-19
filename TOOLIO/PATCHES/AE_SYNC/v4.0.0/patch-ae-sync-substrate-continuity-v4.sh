#!/usr/bin/env bash
set -Eeuo pipefail

TARGET="${AE_SYNC_BIN:-$HOME/.local/bin/ae-sync}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="${TARGET}.bak.${STAMP}.substrate-v4"

echo "============================================================"
echo " ÆTHER // AE-SYNC SUBSTRATE CONTINUITY V4 PATCH"
echo "============================================================"
echo "TARGET=$TARGET"

test -f "$TARGET" || {
    echo "PATCH_ABORT=AE_SYNC_NOT_FOUND|$TARGET" >&2
    exit 10
}

test -w "$TARGET" || {
    echo "PATCH_ABORT=AE_SYNC_NOT_WRITABLE|$TARGET" >&2
    exit 11
}

cp -p "$TARGET" "$BACKUP"
echo "BACKUP=$BACKUP"

rollback_on_failure() {
    local rc="$?"
    if [[ "$rc" -ne 0 ]]; then
        cp -p "$BACKUP" "$TARGET"
        echo "PATCH_ROLLBACK=RESTORED|$BACKUP" >&2
    fi
    return "$rc"
}

trap rollback_on_failure EXIT

python3 - "$TARGET" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")

MARKER = "# AE_SYNC_SUBSTRATE_CONTINUITY_V4_BEGIN"

helper_block = r'''
# AE_SYNC_SUBSTRATE_CONTINUITY_V4_BEGIN
#
# Continuity/reconciliation umbrella:
# physical + logical + cognitive + runtime + interface + routing
# + filesystem + provenance + external projection.
#
# Doctrine: preserve roles. Do not flatten substrates into replicas.
#

AE_SYNC_SUBSTRATE_VERSION=4

path_state() {
    local P="${1:-}"

    if [[ -z "$P" || "$P" == "UNRESOLVED" || "$P" == "DECLARED" ]]; then
        echo "UNRESOLVED"
    elif [[ -e "$P" ]]; then
        echo "PRESENT"
    else
        echo "ABSENT"
    fi
}

aevps_reachability() {
    if ssh -o BatchMode=yes -o ConnectTimeout=5 "$AEVPS" \
        'test -d /opt/AETHIEAOPSYS' >/dev/null 2>&1
    then
        echo "REACHABLE"
    else
        echo "UNREACHABLE"
    fi
}

registry_row() {
    local OUT="$1"
    shift

    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$@" >> "$OUT"
}

write_operator_topology() {
    local OUT="$1"

    cat > "$OUT" <<'EOF'
HUMAN OPERATOR
intent / authority
↓
MIDDLEWARE
interpretation / routing / computation
↓
TOOLS + RUNTIMES + MODELS

OPERATOR = intent + authorization
AÆ       = interpretation
UÆR      = placement / routing
AÆR      = execution gate
MODEL    = cognitive capability
TOOLS    = callable capability
RUNTIME  = execution substrate
AERAG    = provenance / receipt

The model is not the sovereign intent-holder. It is a computational/cognitive substrate under a human-in-the-loop authority structure.

The architecture is operator-authoritative, human-in-the-loop tool topology, where the model is middleware/cognition and does not independently acquire the operator's authority merely because it can interpret or execute instructions.

Abliterated refers separately to a model whose learned refusal behavior has been deliberately weakened or removed at the model level.
EOF
}

write_substrate_registry() {
    local OUT="$1"
    local AUTH_ROOT
    local AEVPS_STATE

    AUTH_ROOT="${AEUSB:-$ROOT}"
    AEVPS_STATE="$(aevps_reachability)"

    printf 'name\tclass\trole\troot_or_endpoint\tauthority_class\texpected_state\tcurrent_state\tdependencies\tupstream\tdownstream\tsync_policy\tverification_method\treceipt_lane\n' > "$OUT"

    registry_row "$OUT" \
        "AEUSB" "BODY_SURFACE" "portable authority / recovery body" \
        "${AEUSB:-UNRESOLVED}" "HOSTLESS_AUTHORITY" "RESOLVED_WHEN_PRESENT" \
        "$(path_state "${AEUSB:-}")" "host resolver" "operator" \
        "AEXHD,RUBIII,AEVPS" "ROLE_AWARE_METADATA_AND_RECEIPT" \
        "body markers + path resolution + packet hash" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "AEXHD" "BODY_SURFACE" "heavy continuity / models / memory" \
        "$AEXHD" "HEAVY_CONTINUITY" "MOUNTED_WHEN_REQUIRED" \
        "$(path_state "$AEXHD")" "aexhd-root" "AEUSB" \
        "runtime routes" "HEAVY_CUSTODY_NO_BLIND_MIRROR" \
        "mount + sidecars + packet hash" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "RUBIII" "BODY_SURFACE" "host execution / local body" \
        "$ROOT" "HOST_EXECUTION" "LOCAL_BODY" "$(path_state "$ROOT")" \
        "host OS" "operator,AEUSB" "tools,runtimes" \
        "HOST_STATE_AND_ROLE_AWARE_PACKET" "path + runtime probe + packet hash" \
        "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "LOLITA" "BODY_SURFACE" "registered host/body" \
        "UNRESOLVED" "REGISTERED_BODY" "DISCOVERABLE" "UNPROBED" \
        "surface registry" "operator" "role-defined" \
        "DISCOVER_BEFORE_SYNC" "surface registry + resolver" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "OLIVIA" "BODY_SURFACE" "registered host/body" \
        "UNRESOLVED" "REGISTERED_BODY" "DISCOVERABLE" "UNPROBED" \
        "surface registry" "operator" "role-defined" \
        "DISCOVER_BEFORE_SYNC" "surface registry + resolver" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "AEVPS" "BODY_SURFACE" "persistent runtime body" \
        "/opt/AETHIEAOPSYS" "PERSISTENT_RUNTIME" "REMOTE_REACHABLE" \
        "$AEVPS_STATE" "ssh" "AEUSB,UÆR" "services,ÆCLOUD" \
        "RUNTIME_STATE_AND_PACKET" "ssh + packet hash" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "AENET" "NETWORK_TRANSPORT" "routing tissue" \
        "$AUTH_ROOT/LAYERS/AENET" "ROUTING_TISSUE" "DECLARED_AND_MATERIALIZED" \
        "$(path_state "$AUTH_ROOT/LAYERS/AENET")" "ROUTES,CONFIG" "UÆR" \
        "Cloudflare,remote compute" "ROUTE_STATE_ONLY" \
        "path + route artifacts" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "Cloudflare" "NETWORK_TRANSPORT" "edge / tunnel / door membrane" \
        "$AUTH_ROOT/TOOLIO/cloudflared" "EXTERNAL_MEMBRANE" "DECLARED_CAPABILITY" \
        "$(path_state "$AUTH_ROOT/TOOLIO/cloudflared")" "AENET" "AENET" \
        "external ingress" "PROJECTION_NO_AUTHORITY_PROMOTION" \
        "local artifacts + external status when explicitly probed" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "TUNNELS" "NETWORK_TRANSPORT" "transport tunnels" \
        "$AUTH_ROOT/CONFIG/network" "TRANSPORT" "DECLARED" \
        "$(path_state "$AUTH_ROOT/CONFIG/network")" "AENET" "routes" \
        "remote endpoints" "ROUTE_STATE_ONLY" "config/path inspection" \
        "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "ROUTES" "NETWORK_TRANSPORT" "declared routes" \
        "$AUTH_ROOT/ROUTES" "ROUTING_DEFINITION" "MATERIALIZED_WHEN_PRESENT" \
        "$(path_state "$AUTH_ROOT/ROUTES")" "AENET,UÆR" "operator" \
        "execution targets" "ROLE_AWARE_METADATA" "path + route manifest" \
        "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "ÆCLOUD" "NETWORK_TRANSPORT" "provider-neutral remote capability" \
        "$AUTH_ROOT/LAYERS/AECLOUD" "REMOTE_CAPABILITY_EXTENSION" \
        "DECLARED_AND_MATERIALIZED" "$(path_state "$AUTH_ROOT/LAYERS/AECLOUD")" \
        "AENET,AEVPS" "AETHIEAOPSYS" "GitHub,GitLab,RunPod" \
        "PROJECTION_ONLY" "path + provider receipts" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "AEPT" "RUNTIME_SERVICE" "declared service substrate" \
        "DECLARED" "SERVICE" "DISCOVERABLE" "UNRESOLVED" \
        "SERVICES" "operator,UÆR" "runtime" "DISCOVER_BEFORE_SYNC" \
        "service registry" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "AEPI" "RUNTIME_SERVICE" "declared service substrate" \
        "DECLARED" "SERVICE" "DISCOVERABLE" "UNRESOLVED" \
        "SERVICES" "operator,UÆR" "runtime" "DISCOVER_BEFORE_SYNC" \
        "service registry" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "AERAG" "RUNTIME_SERVICE" "memory / provenance service" \
        "$AUTH_ROOT/AERAG" "PROVENANCE_SERVICE" "DECLARED_OR_MATERIALIZED" \
        "$(path_state "$AUTH_ROOT/AERAG")" "DATA,MEMORY" "operator,AÆ" \
        "retrieval,receipts" "PROVENANCE_FIRST" "path + receipt state" \
        "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "AESCRAPE" "RUNTIME_SERVICE" "declared scrape / acquisition service" \
        "DECLARED" "SERVICE" "DISCOVERABLE" "UNRESOLVED" \
        "SERVICES" "operator,UÆR" "DATA" "DISCOVER_BEFORE_SYNC" \
        "service registry" "ONE_ACCORD/RECEIPTS"

    for SPEC in \
        "TOOLIO|$AUTH_ROOT/TOOLIO|capability/tool substrate" \
        "DOMAINS|$AUTH_ROOT/DOMAINS|domain/identity substrate" \
        "LAYERS|$AUTH_ROOT/LAYERS|interpretation/abstraction substrate" \
        "HABITAT|$AUTH_ROOT/GCR/HABITAT|environment/workspace substrate" \
        "CORE|$AUTH_ROOT/CORE|core system substrate" \
        "DATA|$AUTH_ROOT/DATA|data substrate" \
        "EXECUTION|$AUTH_ROOT/EXECUTION|execution substrate" \
        "GCR|$AUTH_ROOT/GCR|governance/control substrate" \
        "MODS|$AUTH_ROOT/MODS|modular cognition substrate" \
        "PROGRAMS|$AUTH_ROOT/PROGRAMS|program substrate" \
        "SYSTEM_ROUTES|$AUTH_ROOT/ROUTES|route-definition substrate" \
        "SERVICES|$AUTH_ROOT/SERVICES|service-definition substrate" \
        "CONFIG|$AUTH_ROOT/CONFIG|configuration substrate" \
        "ENV|$AUTH_ROOT/ENV|environment-definition substrate" \
        "LOGS|$AUTH_ROOT/LOGS|observability/log substrate" \
        "SEALS|$AUTH_ROOT/SEALS|seal/integrity substrate" \
        "VAULT|$AUTH_ROOT/VAULT|bounded secret/auth substrate"
    do
        IFS='|' read -r NAME PATH_ ROLE_ <<< "$SPEC"
        registry_row "$OUT" \
            "$NAME" "SYSTEM_ANATOMY" "$ROLE_" "$PATH_" \
            "GOVERNED_COMPONENT" "ROLE_DEFINED" "$(path_state "$PATH_")" \
            "AETHIEAOPSYS" "AEUSB authority or host fallback" "dependent substrates" \
            "METADATA_HASH_RECEIPT_NO_FLATTENING" "path + manifest + packet hash" \
            "ONE_ACCORD/RECEIPTS"
    done

    registry_row "$OUT" \
        "AÆ" "COGNITION_CONTROL" "interpretation" \
        "$AUTH_ROOT/LAYERS/AAE" "COGNITION_NO_INTENT_AUTHORITY" "ROLE_DEFINED" \
        "$(path_state "$AUTH_ROOT/LAYERS/AAE")" "operator input" "OPERATOR" \
        "UÆR" "STATE_ONLY" "path + doctrine" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "UÆR" "COGNITION_CONTROL" "routing / placement" \
        "$AUTH_ROOT/LAYERS/UAER" "ROUTING_NO_INTENT_AUTHORITY" "ROLE_DEFINED" \
        "$(path_state "$AUTH_ROOT/LAYERS/UAER")" "AÆ,AESOFT" "AÆ" \
        "AÆR" "STATE_ONLY" "path + doctrine" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "AÆR" "COGNITION_CONTROL" "execution gate" \
        "DECLARED" "EXECUTION_GATE_NO_INTENT_AUTHORITY" "ROLE_DEFINED" \
        "UNRESOLVED" "UÆR" "UÆR" "runtime" "STATE_ONLY" \
        "doctrine + execution receipts" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "BÆ mesh" "COGNITION_CONTROL" "bounded distributed cognition" \
        "$AUTH_ROOT/MODS/B43-RU5" "BOUNDED_COGNITION" "ROLE_DEFINED" \
        "$(path_state "$AUTH_ROOT/MODS/B43-RU5")" "MODS" "AÆ" \
        "bounded lenses" "STATE_ONLY" "node configs + roles" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "Monocle" "COGNITION_CONTROL" "bounded cognition surface" \
        "DECLARED" "BOUNDED_COGNITION" "DISCOVERABLE" "UNRESOLVED" \
        "AÆ" "operator" "interpretation" "STATE_ONLY" \
        "declared surface registry" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "AERAG_MEMORY" "MEMORY_PROVENANCE" "memory / provenance" \
        "$AUTH_ROOT/AERAG" "PROVENANCE" "DECLARED_OR_MATERIALIZED" \
        "$(path_state "$AUTH_ROOT/AERAG")" "DATA" "execution results" \
        "retrieval" "PROVENANCE_FIRST" "receipt + manifest" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "ONE_ACCORD" "MEMORY_PROVENANCE" "continuity reconciliation packets" \
        "$ONE_RUBIII" "RECONCILIATION_LEDGER" "MATERIALIZED" \
        "$(path_state "$ONE_RUBIII")" "ae-sync" "all substrates" \
        "continuity consumers" "HASHED_PACKET" "SHA256SUMS" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "MANIFESTS" "MEMORY_PROVENANCE" "manifest state" \
        "ONE_ACCORD/*/MANIFESTS" "PROVENANCE" "GENERATED_PER_PACKET" \
        "GENERATED" "ONE_ACCORD" "substrate discovery" "verification" \
        "HASHED_PACKET" "SHA256SUMS" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "RECEIPTS" "MEMORY_PROVENANCE" "receipt state" \
        "ONE_ACCORD/*/RECEIPTS" "PROVENANCE" "GENERATED_PER_PACKET" \
        "GENERATED" "ONE_ACCORD" "verification" "temporal continuity" \
        "HASHED_PACKET" "SHA256SUMS" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "HASHES" "MEMORY_PROVENANCE" "integrity evidence" \
        "ONE_ACCORD/*/SHA256SUMS" "INTEGRITY" "GENERATED_PER_PACKET" \
        "GENERATED" "ONE_ACCORD" "all packet files" "verification" \
        "HASHED_PACKET" "sha256sum -c" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "TEMPORAL_CONTINUITY" "MEMORY_PROVENANCE" "timestamp ordering / continuity" \
        "ONE_ACCORD packet timestamps" "TEMPORAL_PROVENANCE" "GENERATED_PER_PACKET" \
        "GENERATED" "UTC clock" "receipts" "history" "APPEND_ONLY_PACKET_HISTORY" \
        "packet name + UTC fields" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "RECONCILIATION_STATE" "MEMORY_PROVENANCE" "expected vs current relationship state" \
        "STATE/substrate-registry.tsv" "RECONCILIATION" "GENERATED_PER_PACKET" \
        "GENERATED" "substrate registry" "all substrates" "system overview" \
        "ROLE_AWARE_RECONCILIATION" "registry + verification" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "AEMCP" "INTERFACE" "machine interface" \
        "aemcp://AEVPS" "BOUNDED_MACHINE_INTERFACE" "DECLARED_CAPABILITY" \
        "${AEVPS_STATE}_SERVICE_UNPROBED" "AEVPS,AETHIEAOPSYS" "operator/tool clients" \
        "declared capabilities" "CAPABILITY_EXPOSURE_ONLY" \
        "service status + receipts" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "AEGUI" "INTERFACE" "operator visual interface" \
        "DECLARED" "OPERATOR_INTERFACE" "DISCOVERABLE" "UNRESOLVED" \
        "AETHIEAOPSYS" "operator" "bounded controls" "INTERFACE_STATE_ONLY" \
        "interface registry" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "GitHub" "PROJECTION_EXTENSION" "public/versioned continuity projection" \
        "$AUTH_ROOT/.git" "EXTERNAL_PROJECTION" "OPTIONAL_CHECKOUT" \
        "$(path_state "$AUTH_ROOT/.git")" "git" "AETHIEAOPSYS" "external versioning" \
        "PROJECTION_NO_AUTHORITY_PROMOTION" "git HEAD/status when present" \
        "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "GitLab" "PROJECTION_EXTENSION" "version-control projection" \
        "$AUTH_ROOT/GITLAB" "EXTERNAL_PROJECTION" "DECLARED_OR_MATERIALIZED" \
        "$(path_state "$AUTH_ROOT/GITLAB")" "git" "AETHIEAOPSYS" "external versioning" \
        "PROJECTION_NO_AUTHORITY_PROMOTION" "path + git state" "ONE_ACCORD/RECEIPTS"

    registry_row "$OUT" \
        "RunPod" "PROJECTION_EXTENSION" "detachable remote GPU execution" \
        "$AUTH_ROOT/ROUTES/RUNPOD.route" "DETACHABLE_COMPUTE" "ROUTE_DECLARED" \
        "$(path_state "$AUTH_ROOT/ROUTES/RUNPOD.route")" "ÆCLOUD,UÆR,AÆR" \
        "AETHIEAOPSYS" "GPU runtime" "ROUTE_AND_RECEIPT_ONLY" \
        "route artifact + provider receipt" "ONE_ACCORD/RECEIPTS"
}

write_system_overview() {
    local OUT="$1"
    local REG="$2"
    local TOTAL PRESENT ABSENT UNRESOLVED

    TOTAL="$(awk 'NR>1 {n++} END {print n+0}' "$REG")"
    PRESENT="$(awk -F '\t' 'NR>1 && $7=="PRESENT" {n++} END {print n+0}' "$REG")"
    ABSENT="$(awk -F '\t' 'NR>1 && $7=="ABSENT" {n++} END {print n+0}' "$REG")"
    UNRESOLVED="$(awk -F '\t' 'NR>1 && ($7 ~ /UNRESOLVED|UNPROBED|UNREACHABLE/) {n++} END {print n+0}' "$REG")"

    cat > "$OUT" <<EOF
AE_SYNC_SUBSTRATE_VERSION=4
AE_SYNC_SCOPE=FULL_SUBSTRATE_GRAPH
AUTHORITY_MODEL=ROLE_PRESERVING
OPERATOR_AUTHORITY=HUMAN_IN_LOOP
MODEL_INTENT_AUTHORITY=NONE
ROLE_ASSIMILATION=NO
BLIND_MIRRORING=NO

PIPELINE=DISCOVER -> RESOLVE SUBSTRATES -> READ ROLES -> READ SYSTEM ANATOMY -> READ SERVICE STATE -> READ ROUTING STATE -> READ INTERFACE STATE -> READ MEMORY / PROVENANCE STATE -> RECONCILE EXPECTED RELATIONSHIPS -> SYNCHRONIZE ROLE-APPROPRIATE STATE -> VERIFY -> RECEIPT -> ONE_ACCORD -> SYSTEM OVERVIEW

SUBSTRATE_TOTAL=$TOTAL
SUBSTRATE_PRESENT=$PRESENT
SUBSTRATE_ABSENT_OBSERVED=$ABSENT
SUBSTRATE_UNRESOLVED_OR_UNPROBED=$UNRESOLVED

NOTE=ABSENT_OR_UNRESOLVED_IS_OBSERVED_STATE_NOT_AUTOMATIC_ROLE_FAILURE
EOF
}

write_continuity_receipt() {
    local OUT="$1"
    local PACK_NAME="$2"

    cat > "$OUT" <<EOF
RECEIPT_TYPE=AE_SYNC_SUBSTRATE_CONTINUITY
VERSION=4
PACK=$PACK_NAME
UTC=$(date -u +%FT%TZ)
SCOPE=FULL_SUBSTRATE_GRAPH
OPERATOR_AUTHORITY=HUMAN_IN_LOOP
MODEL_INTENT_AUTHORITY=NONE
ROLE_DISTINCTION=PRESERVED
ROLE_ASSIMILATION=NO
BLIND_MIRRORING=NO
EOF
}

verify_packet_contract() {
    local DIR="$1"

    test -s "$DIR/STATE/substrate-registry.tsv" ||
        die "SUBSTRATE_REGISTRY_MISSING:$DIR"

    test -s "$DIR/STATE/operator-topology-preamble.txt" ||
        die "OPERATOR_TOPOLOGY_MISSING:$DIR"

    test -s "$DIR/STATE/system-overview.txt" ||
        die "SYSTEM_OVERVIEW_MISSING:$DIR"

    grep -Fx "SYNC_SCOPE=FULL_SUBSTRATE_GRAPH" \
        "$DIR/STATE/ONE_ACCORD.env" >/dev/null ||
        die "SYNC_SCOPE_CONTRACT_MISSING:$DIR"

    grep -Fx "MODEL_INTENT_AUTHORITY=NONE" \
        "$DIR/STATE/ONE_ACCORD.env" >/dev/null ||
        die "MODEL_AUTHORITY_CONTRACT_MISSING:$DIR"
}

registry_current() {
    local TMP_REG
    TMP_REG="$(mktemp)"

    write_substrate_registry "$TMP_REG"

    if command -v column >/dev/null 2>&1; then
        column -t -s $'\t' "$TMP_REG"
    else
        cat "$TMP_REG"
    fi

    rm -f "$TMP_REG"
}

overview_current() {
    local TMP_REG TMP_OV
    TMP_REG="$(mktemp)"
    TMP_OV="$(mktemp)"

    write_substrate_registry "$TMP_REG"
    write_system_overview "$TMP_OV" "$TMP_REG"
    cat "$TMP_OV"

    rm -f "$TMP_REG" "$TMP_OV"
}

# AE_SYNC_SUBSTRATE_CONTINUITY_V4_END
'''

if MARKER not in s:
    needle = "\nusage() {\n"
    if needle not in s:
        raise SystemExit("PATCH_ABORT=usage_function_anchor_missing")
    s = s.replace(needle, "\n" + helper_block + "\nusage() {\n", 1)

help_anchor = "ae-sync dry-run      Show resolved topology; make no changes\n"
help_add = (
    "ae-sync registry     Discover and print the current substrate registry\n"
    "ae-sync overview     Print the current full-substrate continuity overview\n"
)
if help_add not in s:
    if help_anchor not in s:
        raise SystemExit("PATCH_ABORT=help_anchor_missing")
    s = s.replace(help_anchor, help_anchor + help_add, 1)

dry_anchor = '    echo "WOULD_SYNC=RUBIII,AEUSB,AEXHD,AEVPS"\n'
dry_add = (
    '    echo "WOULD_RECONCILE=FULL_SUBSTRATE_GRAPH"\n'
    '    echo "SUBSTRATE_CLASSES=BODIES,NETWORK,RUNTIME,SYSTEM_ANATOMY,COGNITION,MEMORY,INTERFACE,PROJECTIONS"\n'
    '    echo "PIPELINE=DISCOVER>RESOLVE>READ_ROLES>READ_ANATOMY>READ_SERVICES>READ_ROUTING>READ_INTERFACES>READ_PROVENANCE>RECONCILE>ROLE_SYNC>VERIFY>RECEIPT>ONE_ACCORD>OVERVIEW"\n'
    '    echo "OPERATOR_AUTHORITY=HUMAN_IN_LOOP"\n'
    '    echo "MODEL_INTENT_AUTHORITY=NONE"\n'
)
if "WOULD_RECONCILE=FULL_SUBSTRATE_GRAPH" not in s:
    if dry_anchor not in s:
        raise SystemExit("PATCH_ABORT=dry_run_anchor_missing")
    s = s.replace(dry_anchor, dry_anchor + dry_add, 1)

s = s.replace(
    '    echo " SYNTHESIZE → SYNC → VERIFY → STATUS"\n',
    '    echo " DISCOVER → RECONCILE → ROLE-SYNC → VERIFY → RECEIPT → ONE_ACCORD"\n',
    1,
)

state_anchor = (
    "    # --------------------------------------------------------\n"
    "    # OPERATING STATE\n"
    "    # --------------------------------------------------------\n"
)
state_insert = r'''    # --------------------------------------------------------
    # FULL SUBSTRATE CONTINUITY STATE
    # --------------------------------------------------------

    write_operator_topology \
        "$TMP/STATE/operator-topology-preamble.txt"

    write_substrate_registry \
        "$TMP/STATE/substrate-registry.tsv"

    write_system_overview \
        "$TMP/STATE/system-overview.txt" \
        "$TMP/STATE/substrate-registry.tsv"

    write_continuity_receipt \
        "$TMP/RECEIPTS/substrate-continuity-v4.receipt" \
        "$PACK"

'''
if "write_operator_topology \\" not in s:
    if state_anchor not in s:
        raise SystemExit("PATCH_ABORT=operating_state_anchor_missing")
    s = s.replace(state_anchor, state_insert + state_anchor, 1)

s = s.replace("ONE_ACCORD_VERSION=3", "ONE_ACCORD_VERSION=4", 1)

doctrine_anchor = "SYNC_MODE=ROLE_AWARE\nBLIND_MIRRORING=NO\n"
doctrine_replace = (
    "SYNC_MODE=ROLE_AWARE\n"
    "SYNC_SCOPE=FULL_SUBSTRATE_GRAPH\n"
    "OPERATOR_AUTHORITY=HUMAN_IN_LOOP\n"
    "MODEL_INTENT_AUTHORITY=NONE\n"
    "ROLE_ASSIMILATION=NO\n"
    "BLIND_MIRRORING=NO\n"
)
if "SYNC_MODE=ROLE_AWARE\nSYNC_SCOPE=FULL_SUBSTRATE_GRAPH\n" not in s:
    if doctrine_anchor not in s:
        raise SystemExit("PATCH_ABORT=doctrine_anchor_missing")
    s = s.replace(doctrine_anchor, doctrine_replace, 1)

hash_anchor = (
    "    # --------------------------------------------------------\n"
    "    # PACKET HASH\n"
    "    # --------------------------------------------------------\n"
)
contract_check = r'''    # --------------------------------------------------------
    # V4 CONTRACT CHECK
    # --------------------------------------------------------

    verify_packet_contract "$TMP"

'''
if 'verify_packet_contract "$TMP"' not in s:
    if hash_anchor not in s:
        raise SystemExit("PATCH_ABORT=packet_hash_anchor_missing")
    s = s.replace(hash_anchor, contract_check + hash_anchor, 1)

verify_anchor = (
    '    test -f "$RUBIII_PACKET/SHA256SUMS" ||\n'
    '        die "RUBIII_PACKET_MISSING"\n'
)
verify_insert = verify_anchor + '\n    verify_packet_contract "$RUBIII_PACKET"\n'
if 'verify_packet_contract "$RUBIII_PACKET"' not in s:
    if verify_anchor not in s:
        raise SystemExit("PATCH_ABORT=verify_current_anchor_missing")
    s = s.replace(verify_anchor, verify_insert, 1)

final_anchor = '    echo "ROLE_DISTINCTION=PRESERVED"\n'
final_add = (
    '    echo "SYNC_SCOPE=FULL_SUBSTRATE_GRAPH"\n'
    '    echo "SUBSTRATE_REGISTRY=PASS"\n'
    '    echo "OPERATOR_AUTHORITY=HUMAN_IN_LOOP"\n'
    '    echo "MODEL_INTENT_AUTHORITY=NONE"\n'
    '    echo "ROLE_ASSIMILATION=NO"\n'
)
if '    echo "SUBSTRATE_REGISTRY=PASS"\n' not in s:
    if final_anchor not in s:
        raise SystemExit("PATCH_ABORT=final_status_anchor_missing")
    s = s.replace(final_anchor, final_anchor + final_add, 1)

case_anchor = '''    dry-run)
        dry_run
        ;;
    help|-h|--help)
'''
case_replace = '''    dry-run)
        dry_run
        ;;
    registry)
        registry_current
        ;;
    overview)
        overview_current
        ;;
    help|-h|--help)
'''
if "    registry)\n        registry_current" not in s:
    if case_anchor not in s:
        raise SystemExit("PATCH_ABORT=case_anchor_missing")
    s = s.replace(case_anchor, case_replace, 1)

p.write_text(s, encoding="utf-8")
print("AE_SYNC_SUBSTRATE_CONTINUITY_V4=PATCHED")
PY

chmod 755 "$TARGET"
bash -n "$TARGET"

echo
echo "=== CONTRACT MARKERS ==="
grep -n \
    -e 'AE_SYNC_SUBSTRATE_CONTINUITY_V4_BEGIN' \
    -e 'ONE_ACCORD_VERSION=4' \
    -e 'SYNC_SCOPE=FULL_SUBSTRATE_GRAPH' \
    -e 'MODEL_INTENT_AUTHORITY=NONE' \
    "$TARGET" | head -40

echo
echo "=== HELP ==="
"$TARGET" help

echo
echo "=== DRY RUN ==="
"$TARGET" dry-run

echo
echo "=== REGISTRY SNAPSHOT ==="
"$TARGET" registry

echo
echo "=== OVERVIEW ==="
"$TARGET" overview

echo
trap - EXIT

echo "============================================================"
echo " PATCH=PASS"
echo " TARGET=$TARGET"
echo " BACKUP=$BACKUP"
echo " NEXT_FULL_RUN=ae-sync"
echo " VERIFY_AFTER_RUN=ae-sync verify"
echo "============================================================"
