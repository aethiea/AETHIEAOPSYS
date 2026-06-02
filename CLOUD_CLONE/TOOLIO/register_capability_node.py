#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(os.environ.get("AETHIEA", Path.cwd())).resolve()

DOCTRINE = {
    "name": "Universal Adapter Doctrine",
    "canonical_compression": (
        "Any external tool, model, API, service, device, runtime, or interface "
        "is integrated into AETHIEAOPSYS through authenticated AENET routing, "
        "bounded execution scope, validator chains, anchor persistence, and "
        "Corp-O continuity logging. Tools do not become the system; they become "
        "routed capabilities operating inside system governance."
    ),
    "invariant": "The tool never owns continuity. AETHIEAOPSYS owns continuity.",
    "tool_definition": {
        "not": "trusted system component",
        "is": "temporary bounded execution capability",
    },
    "universal_flow": [
        "identity",
        "route",
        "policy",
        "runtime",
        "memory",
        "validation",
        "audit",
    ],
    "routing_chain": [
        "External Capability",
        "Authentication Layer",
        "AENET Route Assignment",
        "GCR Boundary Resolution",
        "Execution Scope",
        "Validator Chain",
        "Memory/Anchor Persistence",
        "Corp-O Record",
    ],
}


DEFAULT_TOOL_NODES = {
    "chatgpt": {
        "type": "ai_model_client",
        "provider": "openai",
        "auth_ref": "OPENAI_API_KEY",
        "aenet_route": "LAYERS/AENET/CAPABILITIES/chatgpt",
        "gcr_zone": ["DOOR", "PEEP_HOLE"],
        "execution_scope": ["reasoning", "drafting", "code_assist", "analysis"],
        "memory_policy": "write summaries and anchors only; no hidden memory authority",
        "validators": ["json_syntax", "route_integrity", "no_secret_persistence"],
    },
    "codex": {
        "type": "terminal_ai_agent",
        "provider": "openai",
        "auth_ref": "OPENAI_API_KEY",
        "aenet_route": "LAYERS/AENET/CAPABILITIES/codex",
        "gcr_zone": ["HABITAT", "DOOR"],
        "execution_scope": ["code_editing", "repo_analysis", "terminal_assist"],
        "memory_policy": "log commands, diffs, summaries, and anchors",
        "validators": ["python_compile", "json_syntax", "route_integrity", "human_approval_gate"],
    },
    "ollama": {
        "type": "local_model_runtime",
        "provider": "local",
        "auth_ref": None,
        "aenet_route": "LAYERS/AENET/CAPABILITIES/ollama",
        "gcr_zone": ["HABITAT", "VAULT"],
        "execution_scope": ["local_inference", "offline_reasoning"],
        "memory_policy": "local-only unless explicitly exported",
        "validators": ["route_integrity", "model_state_check"],
    },
    "n8n": {
        "type": "automation_runtime",
        "provider": "self_hosted_or_cloud",
        "auth_ref": "N8N_API_KEY",
        "aenet_route": "LAYERS/AENET/CAPABILITIES/n8n",
        "gcr_zone": ["DOOR", "HABITAT"],
        "execution_scope": ["workflow_automation", "webhook_routing"],
        "memory_policy": "log workflow id, input class, output class, and result anchor",
        "validators": ["webhook_scope_check", "route_integrity", "human_approval_gate"],
    },
    "runway": {
        "type": "media_generation_api",
        "provider": "runway",
        "auth_ref": "RUNWAY_API_KEY",
        "aenet_route": "LAYERS/AENET/CAPABILITIES/runway",
        "gcr_zone": ["WINDOW", "DOOR"],
        "execution_scope": ["video_generation", "visual_asset_processing"],
        "memory_policy": "store prompts, output metadata, asset references, and license notes",
        "validators": ["asset_route_check", "metadata_check", "no_secret_persistence"],
    },
    "huggingface": {
        "type": "model_hub_api",
        "provider": "huggingface",
        "auth_ref": "HF_TOKEN",
        "aenet_route": "LAYERS/AENET/CAPABILITIES/huggingface",
        "gcr_zone": ["HABITAT", "DOOR"],
        "execution_scope": ["model_download", "inference", "dataset_reference"],
        "memory_policy": "store model refs, hashes, and source metadata",
        "validators": ["model_ref_check", "hash_check", "route_integrity"],
    },
}


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_slug(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("/", "_")


def build_node(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    slug = safe_slug(name)
    now = utc_stamp()

    return {
        "id": slug,
        "name": name,
        "registered_at_utc": now,
        "status": "registered",
        "doctrine": "Universal Adapter Doctrine",
        "classification": "authenticated_routed_capability",
        "continuity_owner": "AETHIEAOPSYS",
        "tool_owns_continuity": False,
        "human_operator_authority": "required_for_execution",
        "type": spec.get("type", "external_capability"),
        "provider": spec.get("provider", "unknown"),
        "auth": {
            "mode": "environment_or_secret_reference",
            "secret_value_stored": False,
            "auth_ref": spec.get("auth_ref"),
        },
        "routing": {
            "entry": "AENET",
            "aenet_route": spec.get("aenet_route", f"LAYERS/AENET/CAPABILITIES/{slug}"),
            "gcr_zone": spec.get("gcr_zone", ["DOOR"]),
            "execution_scope": spec.get("execution_scope", []),
            "chain": DOCTRINE["routing_chain"],
        },
        "memory": {
            "policy": spec.get("memory_policy", "store summaries, anchors, and audit records only"),
            "writes_to": [
                f"DATA/MEMORY/CAPABILITIES/{slug}/registry.json",
                f"DATA/MEMORY/CAPABILITIES/{slug}/state.json",
                f"DATA/MEMORY/ANCHORS/<timestamp>.json",
            ],
            "raw_logs_to": f"LOGS/CAPABILITIES/{slug}/",
        },
        "validation": {
            "validators": spec.get("validators", ["route_integrity", "no_secret_persistence"]),
            "pass_requires": [
                "route exists",
                "GCR scope declared",
                "execution scope declared",
                "no secret values stored",
                "operator authority preserved",
            ],
        },
        "audit": {
            "corp_o_record_required": True,
            "anchor_required": True,
            "report_required": True,
        },
    }


def register_tool(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    slug = safe_slug(name)
    node = build_node(name, spec)

    capability_root = ROOT / "LAYERS/AENET/CAPABILITIES" / slug
    memory_root = ROOT / "DATA/MEMORY/CAPABILITIES" / slug
    log_root = ROOT / "LOGS/CAPABILITIES" / slug
    tool_root = ROOT / "TOOLIO/CAPABILITIES" / slug

    for folder in [capability_root, memory_root, log_root, tool_root]:
        folder.mkdir(parents=True, exist_ok=True)

    write_json(capability_root / "route.json", node["routing"])
    write_json(capability_root / "policy.json", {
        "tool_id": slug,
        "doctrine": DOCTRINE["name"],
        "gcr_zone": node["routing"]["gcr_zone"],
        "execution_scope": node["routing"]["execution_scope"],
        "secret_value_storage": "forbidden",
        "human_operator_authority": node["human_operator_authority"],
    })
    write_json(memory_root / "registry.json", node)
    write_json(memory_root / "state.json", {
        "tool_id": slug,
        "status": "registered",
        "last_seen_utc": node["registered_at_utc"],
        "continuity_owner": "AETHIEAOPSYS",
    })

    readme = f"""# {name}

Classification: authenticated routed capability

Invariant:
The tool never owns continuity. AETHIEAOPSYS owns continuity.

Route:
{node["routing"]["aenet_route"]}

GCR:
{", ".join(node["routing"]["gcr_zone"])}

Execution scope:
{", ".join(node["routing"]["execution_scope"])}

Auth ref:
{node["auth"]["auth_ref"]}

Secret values are not stored here.
"""
    (tool_root / "README.md").write_text(readme, encoding="utf-8")

    return node


def main() -> None:
    parser = argparse.ArgumentParser(description="Register universal routed capability nodes in AETHIEAOPSYS.")
    parser.add_argument("--tool", help="Register one tool by name. Example: --tool chatgpt")
    parser.add_argument("--type", default="external_capability")
    parser.add_argument("--provider", default="unknown")
    parser.add_argument("--auth-ref", default=None)
    parser.add_argument("--gcr", default="DOOR", help="Comma-separated GCR zones. Example: DOOR,HABITAT")
    parser.add_argument("--scope", default="", help="Comma-separated execution scope.")
    parser.add_argument("--defaults", action="store_true", help="Register default known tool nodes.")
    args = parser.parse_args()

    doctrine_path = ROOT / "DATA/MEMORY/ROUTES/universal_adapter_doctrine.json"
    registry_path = ROOT / "DATA/MEMORY/ROUTES/capability_registry.json"
    anchor_path = ROOT / "DATA/MEMORY/ANCHORS" / f"{utc_stamp()}_universal_adapter_doctrine.json"

    write_json(doctrine_path, DOCTRINE)

    registered: dict[str, Any] = {}

    if args.defaults:
        for name, spec in DEFAULT_TOOL_NODES.items():
            registered[safe_slug(name)] = register_tool(name, spec)

    if args.tool:
        spec = {
            "type": args.type,
            "provider": args.provider,
            "auth_ref": args.auth_ref,
            "gcr_zone": [x.strip().upper() for x in args.gcr.split(",") if x.strip()],
            "execution_scope": [x.strip() for x in args.scope.split(",") if x.strip()],
            "memory_policy": "store summaries, anchors, state, and audit records only",
            "validators": ["route_integrity", "no_secret_persistence", "human_approval_gate"],
        }
        registered[safe_slug(args.tool)] = register_tool(args.tool, spec)

    existing = {}
    if registry_path.exists():
        try:
            existing = json.loads(registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}

    merged = {
        "updated_at_utc": utc_stamp(),
        "doctrine": DOCTRINE["name"],
        "continuity_owner": "AETHIEAOPSYS",
        "tools": {
            **existing.get("tools", {}),
            **registered,
        },
    }

    write_json(registry_path, merged)

    anchor_obj = {
        "timestamp_utc": utc_stamp(),
        "event": "Universal Adapter Doctrine registered systemwide",
        "root": str(ROOT),
        "doctrine_path": str(doctrine_path.relative_to(ROOT)),
        "registry_path": str(registry_path.relative_to(ROOT)),
        "registered_tools": sorted(registered.keys()),
        "hash": sha256_text(json.dumps(merged, sort_keys=True)),
    }
    write_json(anchor_path, anchor_obj)

    print("=== AETHIEA UNIVERSAL ADAPTER PATCH ===")
    print(f"ROOT: {ROOT}")
    print(f"DOCTRINE: {doctrine_path.relative_to(ROOT)}")
    print(f"REGISTRY: {registry_path.relative_to(ROOT)}")
    print(f"ANCHOR: {anchor_path.relative_to(ROOT)}")
    print(f"REGISTERED: {', '.join(sorted(registered.keys())) if registered else 'doctrine only'}")
    print("STATUS: OK")


if __name__ == "__main__":
    main()
