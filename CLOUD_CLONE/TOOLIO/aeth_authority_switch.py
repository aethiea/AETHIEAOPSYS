#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, os, socket, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_AUTHORITY = "DNY-5U5"

CONTROL_FILE = Path("CORE/AUTHORITY/authority_switch.json")
LOG_FILE = Path("LOGS/AUTHORITY/authority_switch.log")
STATE_DIR = Path("DATA/MEMORY/STATE/AUTHORITY")

TARGET_ROOTS = [
    "MODS/B43-RU5",
    "MODS/P47H30N/NODES",
    "LAYERS",
    "DOMAINS",
    "EXECUTION/PIPELINES",
    "GCR",
]


def root() -> Path:
    return Path(os.environ.get("AETHIEA", Path.cwd())).resolve()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure(base: Path) -> None:
    for p in [base / CONTROL_FILE.parent, base / LOG_FILE.parent, base / STATE_DIR]:
        p.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, fallback: Any = None) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def digest(data: Any) -> str:
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def safe_name(target: str) -> str:
    return target.strip("./").replace("/", "_").replace(" ", "_").replace(":", "_")


def build_state(args: argparse.Namespace) -> dict[str, Any]:
    state = {
        "authority": args.authority,
        "context": args.context.upper(),
        "switch_active": True,
        "scope": args.scope,
        "targets": args.targets,
        "operator_directive": args.directive,
        "host": socket.gethostname(),
        "timestamp_utc": now(),
        "rule": "Script does not decide policy. Script broadcasts operator-declared authority context into AETHIEAOPSYS runtime.",
        "structural_paths": {
            "authority_truth": str(CONTROL_FILE),
            "inherited_state": str(STATE_DIR),
            "audit_log": str(LOG_FILE),
        },
    }
    state["event_hash"] = digest(state)
    return state


def log_event(base: Path, payload: dict[str, Any]) -> None:
    with (base / LOG_FILE).open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def set_context(args: argparse.Namespace) -> None:
    base = root()
    ensure(base)

    state = build_state(args)
    payload = {
        "authority_switch": state,
        "inheritance": {
            "all_targets_inherit_operator_context": True,
            "script_imposes_policy": False,
            "script_decides_permissions": False,
            "operator_is_authority_source": True,
        },
    }

    write_json(base / CONTROL_FILE, payload)
    log_event(base, {"event": "SET_CONTEXT", **state})

    print("[AUTHORITY SWITCH] SET")
    print(f"context:   {state['context']}")
    print(f"authority: {state['authority']}")
    print(f"scope:     {state['scope']}")
    print(f"hash:      {state['event_hash']}")


def off(args: argparse.Namespace) -> None:
    base = root()
    ensure(base)

    state = {
        "authority": args.authority,
        "context": args.context.upper(),
        "switch_active": False,
        "scope": args.scope,
        "targets": args.targets,
        "operator_directive": args.directive,
        "host": socket.gethostname(),
        "timestamp_utc": now(),
        "rule": "Switch off records operator-declared fallback context. Script imposes no policy.",
    }
    state["event_hash"] = digest(state)

    payload = {
        "authority_switch": state,
        "inheritance": {
            "all_targets_inherit_operator_context": True,
            "script_imposes_policy": False,
            "script_decides_permissions": False,
            "operator_is_authority_source": True,
        },
    }

    write_json(base / CONTROL_FILE, payload)
    log_event(base, {"event": "SWITCH_OFF", **state})

    print("[AUTHORITY SWITCH] OFF")
    print(f"context: {state['context']}")


def current_state(base: Path) -> dict[str, Any]:
    payload = read_json(base / CONTROL_FILE)
    if not payload:
        raise SystemExit("No authority state found. Run: aeth_authority_switch.py set SANDBOX")
    return payload["authority_switch"]


def apply_one(base: Path, target: str, state: dict[str, Any]) -> Path:
    out = {
        "target": target,
        "inherits_from_authority_switch": True,
        "authority": state["authority"],
        "context": state["context"],
        "switch_active": state["switch_active"],
        "scope": state["scope"],
        "operator_directive": state.get("operator_directive", ""),
        "source_event_hash": state.get("event_hash", ""),
        "timestamp_utc": now(),
        "rule": "Target inherits operator-declared context. Script imposes no policy.",
    }
    out["inheritance_hash"] = digest(out)

    file = base / STATE_DIR / f"{safe_name(target)}.json"
    write_json(file, out)
    return file


def apply(args: argparse.Namespace) -> None:
    base = root()
    ensure(base)
    state = current_state(base)

    file = apply_one(base, args.target, state)
    log_event(base, {"event": "APPLY_TARGET", "target": args.target, "file": str(file), **state})

    print("[AUTHORITY CONTEXT APPLIED]")
    print(f"target:  {args.target}")
    print(f"context: {state['context']}")
    print(f"file:    {file}")


def discover_targets(base: Path) -> list[str]:
    targets: list[str] = []

    for root_name in TARGET_ROOTS:
        r = base / root_name
        if not r.exists():
            continue

        if root_name == "MODS/B43-RU5":
            for p in sorted(r.iterdir()):
                if p.is_dir() and p.name.isdigit():
                    targets.append(str(p.relative_to(base)))
            continue

        if root_name == "MODS/P47H30N/NODES":
            for p in sorted(r.iterdir()):
                if p.is_dir():
                    targets.append(str(p.relative_to(base)))
            continue

        for p in sorted(r.iterdir()):
            if p.is_dir():
                targets.append(str(p.relative_to(base)))

    return targets


def apply_all(_: argparse.Namespace) -> None:
    base = root()
    ensure(base)
    state = current_state(base)

    targets = discover_targets(base)
    files = [apply_one(base, target, state) for target in targets]

    log_event(base, {
        "event": "APPLY_ALL",
        "count": len(files),
        "targets": targets,
        **state,
    })

    print("[AUTHORITY CONTEXT APPLIED ALL]")
    print(f"context: {state['context']}")
    print(f"targets: {len(files)}")
    print(f"state_dir: {base / STATE_DIR}")


def status(_: argparse.Namespace) -> None:
    base = root()
    payload = read_json(base / CONTROL_FILE)
    if not payload:
        print("[AUTHORITY SWITCH] no state found")
        return
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def main() -> None:
    p = argparse.ArgumentParser(prog="aeth-authority-switch")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("set")
    s.add_argument("context")
    s.add_argument("--authority", default=DEFAULT_AUTHORITY)
    s.add_argument("--scope", default="GLOBAL")
    s.add_argument("--targets", default="ALL")
    s.add_argument("--directive", default="operator declared authority context")
    s.set_defaults(func=set_context)

    o = sub.add_parser("off")
    o.add_argument("--context", default="SANDBOX")
    o.add_argument("--authority", default=DEFAULT_AUTHORITY)
    o.add_argument("--scope", default="GLOBAL")
    o.add_argument("--targets", default="ALL")
    o.add_argument("--directive", default="operator switched authority context off")
    o.set_defaults(func=off)

    a = sub.add_parser("apply")
    a.add_argument("target")
    a.set_defaults(func=apply)

    aa = sub.add_parser("apply-all")
    aa.set_defaults(func=apply_all)

    st = sub.add_parser("status")
    st.set_defaults(func=status)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
