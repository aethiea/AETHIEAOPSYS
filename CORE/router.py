from __future__ import annotations
import os
from pathlib import Path
ROOT = Path(os.environ.get("AETHIEA", Path.cwd()))

import json
from state import resolve_path


AETHIEA = os.environ.get("AETHIEA", "")


def load_json(rel_path: str) -> dict:
    full = os.path.join(AETHIEA, rel_path)
    with open(full, "r", encoding="utf-8") as f:
        return json.load(f)


def route_layer(layer: str) -> dict:
    layer_key = layer.upper()
    data = load_json("DATA/MEMORY/ROUTES/layer_map.json")

    if layer_key not in data:
        return {
            "target": "LAYERS",
            "path": str(resolve_path("layers")),
            "action": "layer_route",
            "status": "unknown_layer",
            "input": layer
        }

    item = data[layer_key]
    return {
        "target": f"LAYERS/{layer_key}",
        "path": os.path.join(AETHIEA, "LAYERS", layer_key),
        "action": "layer_route",
        "role": item.get("role"),
        "routes_to": item.get("routes_to", []),
        "status": "ok"
    }


def route_domain(domain: str) -> dict:
    domain_key = domain.upper()
    data = load_json("DATA/MEMORY/ROUTES/domain_gcr_execution_map.json")

    if domain_key not in data:
        return {
            "target": "DOMAINS",
            "path": os.path.join(AETHIEA, "DOMAINS"),
            "action": "domain_route",
            "status": "unknown_domain",
            "input": domain
        }

    item = data[domain_key]
    return {
        "target": f"DOMAINS/{domain_key}",
        "path": os.path.join(AETHIEA, "DOMAINS", domain_key),
        "action": "domain_route",
        "default_gcr": item.get("default_gcr", []),
        "execution_allowed": item.get("execution_allowed"),
        "execution_targets": item.get("execution_targets", []),
        "constraint": item.get("constraint", ""),
        "status": "ok"
    }



def simulate_route(domain: str) -> dict:
    domain_key = domain.upper()
    domain_map = load_json("DATA/MEMORY/ROUTES/domain_gcr_execution_map.json")

    if domain_key not in domain_map:
        return {
            "target": "ROUTE_SIMULATION",
            "action": "simulate_route",
            "status": "denied",
            "reason": "unknown_domain",
            "autonomy_loop": "UAER → AAE → AENET → DENIED",
            "input": domain
        }

    item = domain_map[domain_key]
    gcr = item.get("default_gcr", [])
    execution_allowed = bool(item.get("execution_allowed"))
    execution_targets = item.get("execution_targets", [])
    constraint = item.get("constraint", "")

    path_chain = [
        "UAER/intake",
        "AAE/pattern_map",
        "AENET/route",
        f"DOMAINS/{domain_key}",
        "GCR/" + "+".join(gcr) if gcr else "GCR/UNDEFINED",
    ]

    if execution_allowed:
        path_chain.extend([
            "B43-RU5/function_node",
            "EXECUTION/" + "+".join(execution_targets) if execution_targets else "EXECUTION/UNDEFINED",
            "DATA/log_feedback"
        ])
        status = "allowed"
    else:
        path_chain.extend([
            "B43-RU5/blocked",
            "EXECUTION/DENIED",
            "DATA/log_denial"
        ])
        status = "denied"

    return {
        "target": f"DOMAINS/{domain_key}",
        "action": "simulate_route",
        "domain": domain_key,
        "autonomy_loop": " → ".join(path_chain),
        "default_gcr": gcr,
        "execution_allowed": execution_allowed,
        "execution_targets": execution_targets,
        "constraint": constraint,
        "status": status
    }


def route_entity(domain: str, entity: str) -> dict:
    domain_key = domain.upper()
    entity_path = os.path.join(AETHIEA, "DOMAINS", domain_key, entity)

    if not os.path.isdir(entity_path):
        return {
            "target": "ENTITY",
            "action": "entity_route",
            "status": "not_found",
            "domain": domain,
            "entity": entity
        }

    binding_file = os.path.join(entity_path, "BINDING.json")

    if not os.path.exists(binding_file):
        return {
            "target": entity_path,
            "action": "entity_route",
            "status": "no_binding",
            "domain": domain,
            "entity": entity
        }

    try:
        with open(binding_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "target": entity_path,
            "action": "entity_route",
            "domain": domain_key,
            "entity": entity,
            "gcr_zone": data.get("gcr_zone", []),
            "layer_path": data.get("layer_path", []),
            "bae_binding": data.get("bae_binding", []),
            "execution_targets": data.get("execution_targets", []),
            "execution_hook": data.get("execution_hook", ""),
            "execution_mode": data.get("execution_mode", ""),
            "allowed_actions": data.get("allowed_actions", []),
            "not_allowed": data.get("not_allowed", []),
            "status": "ok"
        }

    except Exception as e:
        return {
            "target": entity_path,
            "action": "entity_route",
            "status": "error",
            "error": str(e)
        }


def simulate_entity(value: str) -> dict:
    if "/" not in value:
        return {
            "target": "ENTITY_SIMULATION",
            "action": "simulate_entity",
            "status": "invalid_args",
            "usage": "simulate entity <DOMAIN/ENTITY>",
            "input": value
        }

    domain, entity = value.split("/", 1)
    domain_key = domain.strip().upper()
    entity_name = entity.strip()

    entity_path = os.path.join(AETHIEA, "DOMAINS", domain_key, entity_name)
    binding_file = os.path.join(entity_path, "BINDING.json")

    if not os.path.isdir(entity_path):
        return {
            "target": "ENTITY_SIMULATION",
            "action": "simulate_entity",
            "status": "not_found",
            "domain": domain_key,
            "entity": entity_name
        }

    if not os.path.isfile(binding_file):
        return {
            "target": entity_path,
            "action": "simulate_entity",
            "status": "no_binding",
            "domain": domain_key,
            "entity": entity_name
        }

    with open(binding_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    gcr = data.get("gcr_zone", [])
    layer_path = data.get("layer_path", [])
    bae_binding = data.get("bae_binding", [])
    execution_targets = data.get("execution_targets", [])
    allowed_actions = data.get("allowed_actions", [])
    not_allowed = data.get("not_allowed", [])

    autonomy_loop = []
    autonomy_loop.extend([f"{x}/process" for x in layer_path])
    autonomy_loop.append(f"DOMAINS/{domain_key}/{entity_name}")
    autonomy_loop.append("GCR/" + "+".join(gcr) if gcr else "GCR/UNDEFINED")
    autonomy_loop.append("B43-RU5/" + "+".join(bae_binding) if bae_binding else "B43-RU5/UNDEFINED")
    autonomy_loop.append("EXECUTION/" + "+".join(execution_targets) if execution_targets else "EXECUTION/UNDEFINED")
    autonomy_loop.append("DATA/log_feedback")

    return {
        "target": entity_path,
        "action": "simulate_entity",
        "domain": domain_key,
        "entity": entity_name,
        "autonomy_loop": " → ".join(autonomy_loop),
        "gcr_zone": gcr,
        "layer_path": layer_path,
        "bae_binding": bae_binding,
        "execution_targets": execution_targets,
        "execution_hook": data.get("execution_hook", ""),
        "execution_mode": data.get("execution_mode", ""),
        "allowed_actions": allowed_actions,
        "not_allowed": not_allowed,
        "status": "allowed"
    }

def route_command(command: str) -> dict:
    raw = command.strip()
    cmd = raw.lower()
    parts = raw.split()

    if cmd in {"status", "sys"}:
        return {"target": "CORE", "path": str(resolve_path("core")), "action": "status"}

    if cmd == "layers":
        return {"target": "LAYERS", "path": str(resolve_path("layers")), "action": "list_layers"}

    if cmd.startswith("layer "):
        return route_layer(raw.split(" ", 1)[1])

    if cmd == "domains":
        return {"target": "DOMAINS", "path": os.path.join(AETHIEA, "DOMAINS"), "action": "list_domains"}

    if cmd.startswith("domain "):
        return route_domain(raw.split(" ", 1)[1])

    if cmd.startswith("simulate entity "):
        return simulate_entity(raw.split(" ", 2)[2])

    if cmd.startswith("simulate "):
        return simulate_route(raw.split(" ", 1)[1])

    if cmd.startswith("entity "):
        value = raw.split(" ", 1)[1]
        if "/" in value:
            domain, entity = value.split("/", 1)
            return route_entity(domain.strip(), entity.strip())
        parts = raw.split(" ", 2)
        if len(parts) < 3:
            return {"action": "entity_route", "status": "invalid_args", "usage": "entity <DOMAIN/ENTITY>"}
        return route_entity(parts[1], parts[2])

    if cmd.startswith("flow "):
        return simulate_route(raw.split(" ", 1)[1])

    if cmd == "mods":
        return {"target": "MODS", "path": str(resolve_path("mods")), "action": "list_mods"}

    if cmd == "nodes":
        return {"target": "P47H30N/NODES", "path": str(resolve_path("nodes")), "action": "list_nodes"}

    if cmd == "routes":
        return {"target": "P47H30N/ROUTES", "path": str(resolve_path("routes")), "action": "list_routes"}

    if cmd == "memory":
        return {"target": "DATA/MEMORY", "path": str(resolve_path("memory")), "action": "memory_list"}

    if cmd.startswith("memory write "):
        return {"target": "DATA/MEMORY", "path": str(resolve_path("memory")), "action": "memory_write"}

    if cmd.startswith("memory read "):
        return {"target": "DATA/MEMORY", "path": str(resolve_path("memory")), "action": "memory_read"}

    return {"target": "UNKNOWN", "path": None, "action": "unknown", "input": raw}

# --- AENET FIRST ROUTES ---
AENET = ROOT / "LAYERS" / "AENET"

def resolve_route(name: str):
    name = (name or "").lower().strip()

    # direct layer hits
    if name in ("network", "aenet", "aethernet"):
        return AENET

    if name == "cloudflare":
        return AENET / "CLOUDFLARE"

    # dynamic AENET subpaths
    candidate = AENET / name.upper()
    if candidate.exists():
        return candidate

    # fallback to existing route table
    routes = build_routes()
    return routes.get(name)

# --- ROUTE LOCK ---
__AENET_ROUTE_LOCK__ = True
