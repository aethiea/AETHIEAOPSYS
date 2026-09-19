# AE-SYNC Substrate Continuity v4 — Patch Notes

## Patch identity

**Patch:** `AE-SYNC SUBSTRATE CONTINUITY V4`  
**Target:** `~/.local/bin/ae-sync` (or `$AE_SYNC_BIN`)  
**Continuity packet:** `ONE_ACCORD`  
**Upgrade:** `ONE_ACCORD_VERSION=3` → `ONE_ACCORD_VERSION=4`

## Why this patch exists

The existing `ae-sync` implementation already performs role-aware ONE_ACCORD packet construction, distribution, cross-body SHA-256 verification, and `LATEST` consensus across RUBIII, AEUSB, AEXHD, and AEVPS.

That is retained.

The missing class is the **internal AETHIEAOPSYS anatomy and the wider substrate graph**. `ae-sync` is therefore upgraded from a body-focused continuity packet into the continuity/reconciliation umbrella for physical, logical, cognitive, runtime, interface, routing, filesystem, provenance, and external-projection substrates.

The patch does **not** turn all substrates into replicas. It records their different roles, expected/current state, dependencies, authority class, verification method, synchronization policy, and receipt lane.

## Canonical lock encoded by v4

`ae-sync` is the continuity/reconciliation umbrella over the entire AETHIEAOPSYS substrate graph while preserving each component's role instead of flattening them into one thing.

The packet now carries these substrate classes:

- `BODY_SURFACE`
- `NETWORK_TRANSPORT`
- `RUNTIME_SERVICE`
- `SYSTEM_ANATOMY`
- `COGNITION_CONTROL`
- `MEMORY_PROVENANCE`
- `INTERFACE`
- `PROJECTION_EXTENSION`

The registry schema is:

```text
SUBSTRATE
├── name
├── class
├── role
├── root / endpoint
├── authority_class
├── expected_state
├── current_state
├── dependencies
├── upstream
├── downstream
├── sync_policy
├── verification_method
└── receipt_lane
```

## Operator-authority continuity preamble

Each v4 packet writes:

```text
STATE/operator-topology-preamble.txt
```

with the continuity preamble:

```text
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
```

The packet contract explicitly records:

```text
OPERATOR_AUTHORITY=HUMAN_IN_LOOP
MODEL_INTENT_AUTHORITY=NONE
ROLE_ASSIMILATION=NO
BLIND_MIRRORING=NO
```

This is an **authority topology statement**. It is separate from any model's alignment/refusal characteristics.

## New generated continuity artifacts

Every full `ae-sync` packet now includes:

```text
STATE/
├── body-map.tsv
├── current-state.txt
├── ONE_ACCORD.env
├── operator-topology-preamble.txt
├── substrate-registry.tsv
└── system-overview.txt

MANIFESTS/
├── aexhd-cold-models.tsv
├── aevps-runtime.tsv
└── rubiii-small-state.tsv

RECEIPTS/
├── substrate-continuity-v4.receipt
└── preserved continuity receipts

SHA256SUMS
```

The new state files are inside the same deterministic packet hash already used by `ae-sync`, so the registry, topology preamble, overview, and receipt are cryptographically bound to the ONE_ACCORD packet.

## Expanded bare `ae-sync` meaning

v4 records the pipeline as:

```text
DISCOVER
→ RESOLVE SUBSTRATES
→ READ ROLES
→ READ SYSTEM ANATOMY
→ READ SERVICE STATE
→ READ ROUTING STATE
→ READ INTERFACE STATE
→ READ MEMORY / PROVENANCE STATE
→ RECONCILE EXPECTED RELATIONSHIPS
→ SYNCHRONIZE ROLE-APPROPRIATE STATE
→ VERIFY
→ RECEIPT
→ ONE_ACCORD
→ SYSTEM OVERVIEW
```

The current patch expands discovery/reconciliation metadata. It intentionally does **not** blindly copy every filesystem lane or external service payload.

## System anatomy registered by v4

The patch registers at least:

```text
TOOLIO
DOMAINS
LAYERS
HABITAT
CORE
DATA
EXECUTION
GCR
MODS
PROGRAMS
ROUTES
SERVICES
CONFIG
ENV
LOGS
SEALS
VAULT
```

`HABITAT` resolves through `GCR/HABITAT` in the current filesystem topology.

## Cognition / control path registered by v4

```text
AÆ       = interpretation
UÆR      = placement / routing
AÆR      = execution gate
BÆ mesh  = bounded distributed cognition
Monocle  = bounded cognition surface
```

A substrate being registered does not mean its current filesystem path is invented. Where a concrete path is not resolved by the current runtime, v4 records `UNRESOLVED` or `UNPROBED` rather than manufacturing one.

## Role preservation

Existing body roles remain:

```text
AEUSB  = portable authority / recovery body
AEXHD  = heavy continuity / models / memory
RUBIII = host execution / local body
AEVPS  = persistent runtime body
```

External surfaces remain projections/extensions rather than automatic authority:

```text
GitHub
GitLab
ÆCLOUD
RunPod
Cloudflare
```

The registry encodes policies such as:

```text
ROLE_AWARE_METADATA_AND_RECEIPT
HEAVY_CUSTODY_NO_BLIND_MIRROR
PROJECTION_NO_AUTHORITY_PROMOTION
ROUTE_AND_RECEIPT_ONLY
METADATA_HASH_RECEIPT_NO_FLATTENING
```

## New commands

```bash
ae-sync registry
```

Discovers and prints the current substrate registry without running a full synchronization packet.

```bash
ae-sync overview
```

Prints the current full-substrate continuity overview.

Existing commands remain:

```bash
ae-sync
ae-sync all
ae-sync status
ae-sync verify
ae-sync history
ae-sync dry-run
ae-sync help
```

The already-established `aeth sync ...` bridge remains compatible because it delegates to `ae-sync`.

## Verification contract

Before hashing a new packet, v4 requires:

```text
STATE/substrate-registry.tsv
STATE/operator-topology-preamble.txt
STATE/system-overview.txt
STATE/ONE_ACCORD.env
```

and validates that `ONE_ACCORD.env` contains:

```text
SYNC_SCOPE=FULL_SUBSTRATE_GRAPH
MODEL_INTENT_AUTHORITY=NONE
```

`ae-sync verify` also checks this v4 contract on the RUBIII source packet before performing cross-body SHA-256 verification.

## Observed state is not automatic failure

A registered substrate can legitimately report:

```text
PRESENT
ABSENT
UNRESOLVED
UNPROBED
UNREACHABLE
GENERATED
```

`ABSENT` or `UNRESOLVED` is an observation, not automatic evidence that the architecture is wrong. This keeps discovery evidence separate from role doctrine and avoids silently inventing state.

## Apply

```bash
chmod +x patch-ae-sync-substrate-continuity-v4.sh
./patch-ae-sync-substrate-continuity-v4.sh
```

The patch creates a timestamped backup before modifying `ae-sync`, installs an automatic rollback-on-failure trap, runs `bash -n`, then prints the help surface, dry-run state, substrate registry, and system overview. The rollback trap is cleared only after all patch checks complete successfully.

## Full continuity run after patch

```bash
ae-sync
ae-sync verify
ae-sync status
```

Or through the native bridge:

```bash
aeth sync
aeth sync verify
aeth sync status
```

## Expected final v4 status additions

A successful full run adds:

```text
SYNC_SCOPE=FULL_SUBSTRATE_GRAPH
SUBSTRATE_REGISTRY=PASS
OPERATOR_AUTHORITY=HUMAN_IN_LOOP
MODEL_INTENT_AUTHORITY=NONE
ROLE_ASSIMILATION=NO
ROLE_DISTINCTION=PRESERVED
ONE_ACCORD=PASS
```

## What v4 deliberately does not do

It does not:

- promote GitHub, GitLab, Cloudflare, RunPod, or another projection into authority;
- make RUBIII the continuity authority merely because it executes the command;
- copy heavy models into every body;
- replicate secrets;
- require identical filesystem semantics across removable bodies;
- treat cognition, routing, interfaces, services, and storage bodies as the same substrate class;
- invent paths for declared components whose current endpoint is not evidenced;
- equate `PRESENT` with callable runtime capacity.

That preserves the existing AETHIEAOPSYS doctrine: **separation with coordination; symbiosis, not assimilation; no body replaces another body.**
