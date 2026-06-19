import json
import os
import py_compile
import subprocess
import sys

AETHIEA = os.environ.get("AETHIEA", "")
HOME = os.path.expanduser("~")

def load(rel_path):
    full_path = os.path.join(AETHIEA, rel_path)
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save(rel_path, data):
    full_path = os.path.join(AETHIEA, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def log_event(message):
    log_path = os.path.join(AETHIEA, "LOGS", "system.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def status():
    system = load("DATA/MEMORY/SYSTEM/aethiea.json")
    state = load("DATA/MEMORY/STATE/current.json")
    session_data = load("DATA/MEMORY/SESSIONS/latest.json")

    print("SYSTEM:", system["system_name"])
    print("HOST:", state["active_host"])
    print("ROOT:", state["system_root"])
    print("PHASE:", state["phase"])
    print("STATUS:", state["status"])
    print("SESSION:", session_data["session_type"])
    print("LAST ACTION:", session_data["last_action"])
    print("NEXT:", session_data["resume_next"])

def hosts():
    state = load("DATA/MEMORY/STATE/current.json")
    current = state.get("active_host", "")
    hosts_dir = os.path.join(AETHIEA, "DATA/MEMORY/HOSTS")

    if not os.path.isdir(hosts_dir):
        print("No hosts directory found")
        return

    for file in sorted(os.listdir(hosts_dir)):
        path = os.path.join(hosts_dir, file)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            name = data.get("host_name", "UNKNOWN")
            root = data.get("system_root", "UNKNOWN")
            status_value = data.get("status", "unknown")
            marker = "* " if name == current else "  "
            print(f"{marker}{name} → {root} ({status_value})")
        except Exception as e:
            print(f"{file} → ERROR: {e}")

def logs():
    log_path = os.path.join(AETHIEA, "LOGS", "system.log")

    if not os.path.isfile(log_path):
        print("No system log found")
        return

    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines[-10:]:
        print(line.rstrip())

def validate():
    checks = []

    required = [
        "DATA/MEMORY/SYSTEM/aethiea.json",
        "DATA/MEMORY/STATE/current.json",
        "DATA/MEMORY/SESSIONS/latest.json",
    ]

    for rel in required:
        full = os.path.join(AETHIEA, rel)
        checks.append((f"exists {rel}", os.path.isfile(full), None if os.path.isfile(full) else "missing"))

    for rel in required:
        full = os.path.join(AETHIEA, rel)
        try:
            with open(full, "r", encoding="utf-8") as f:
                json.load(f)
            checks.append((f"json {rel}", True, None))
        except Exception as e:
            checks.append((f"json {rel}", False, str(e)))

    py_files = [
        os.path.join(AETHIEA, "CORE", "aeth.py"),
        os.path.join(AETHIEA, "CORE", "read_memory.py"),
    ]

    for full in py_files:
        try:
            py_compile.compile(full, doraise=True)
            checks.append((f"python {full}", True, None))
        except Exception as e:
            checks.append((f"python {full}", False, str(e)))

    host_tools = [
        os.path.join(HOME, ".local", "bin", "aeth-up"),
        os.path.join(HOME, ".local", "bin", "aeth-run"),
    ]

    for full in host_tools:
        checks.append((f"exists {full}", os.path.isfile(full), None if os.path.isfile(full) else "missing"))

    failures = 0
    for name, ok, detail in checks:
        if ok:
            print(f"OK   {name}")
        else:
            failures += 1
            print(f"FAIL {name} :: {detail}")

    if failures == 0:
        print("VALIDATION: PASS")
    else:
        print(f"VALIDATION: FAIL ({failures} issue(s))")
        sys.exit(1)

def session():
    data = load("DATA/MEMORY/SESSIONS/latest.json")
    print("HOST:", data.get("host", "UNKNOWN"))
    print("ROOT:", data.get("system_root", "UNKNOWN"))
    print("SESSION TYPE:", data.get("session_type", "UNKNOWN"))
    print("LAST ACTION:", data.get("last_action", "UNKNOWN"))
    print("NEXT:", data.get("resume_next", "UNKNOWN"))
    print("HANDOFF READY:", data.get("handoff_ready", "UNKNOWN"))

def anchor():
    anchors_dir = os.path.join(AETHIEA, "DATA/MEMORY/ANCHORS")

    if not os.path.isdir(anchors_dir):
        print("No anchors directory found")
        return

    for file in sorted(os.listdir(anchors_dir)):
        path = os.path.join(anchors_dir, file)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"{data.get('date', file)} → {data.get('event', 'UNKNOWN EVENT')}")
        except Exception as e:
            print(f"{file} → ERROR: {e}")

def scan():
    print("=== SHELL ===")
    for target in [
        os.path.join(HOME, ".bashrc"),
        os.path.join(HOME, ".local", "bin", "aeth-up"),
        os.path.join(HOME, ".local", "bin", "aeth-run"),
    ]:
        if os.path.isfile(target):
            result = subprocess.run(["bash", "-n", target], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"OK   shell {target}")
            else:
                print(f"FAIL shell {target}")
                print(result.stderr.strip())

    print("=== PYTHON ===")
    for target in [
        os.path.join(AETHIEA, "CORE", "aeth.py"),
        os.path.join(AETHIEA, "CORE", "read_memory.py"),
    ]:
        try:
            py_compile.compile(target, doraise=True)
            print(f"OK   python {target}")
        except Exception as e:
            print(f"FAIL python {target} :: {e}")

    print("=== JSON MEMORY ===")
    memory_root = os.path.join(AETHIEA, "DATA", "MEMORY")
    for root, _, files in os.walk(memory_root):
        for file in sorted(files):
            if file.endswith(".json"):
                full = os.path.join(root, file)
                try:
                    with open(full, "r", encoding="utf-8") as f:
                        json.load(f)
                    print(f"OK   json {full}")
                except Exception as e:
                    print(f"FAIL json {full} :: {e}")

    print("=== COMMAND RESOLUTION ===")
    print("Run in shell if needed: type aeth ; type aethcd ; alias aeth 2>/dev/null")

def write_value(target, key, value):
    target_map = {
        "state": "DATA/MEMORY/STATE/current.json",
        "session": "DATA/MEMORY/SESSIONS/latest.json",
    }

    if target not in target_map:
        print("write target must be: state or session")
        sys.exit(1)

    rel_path = target_map[target]
    data = load(rel_path)
    data[key] = value
    save(rel_path, data)

    log_event(f"WRITE target={target} key={key} value={value}")

    print(f"WROTE {target}.{key} = {value}")


from datetime import datetime, timezone

def write_anchor(event):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    filename = f"{ts}.json"
    path = os.path.join(AETHIEA, "DATA/MEMORY/ANCHORS", filename)

    data = {
        "timestamp": ts,
        "event": event
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    log_event(f"ANCHOR {event} {ts}")
    print(f"ANCHOR CREATED → {filename}")


def anchor_find(term):
    anchors_dir = os.path.join(AETHIEA, "DATA/MEMORY/ANCHORS")

    if not os.path.isdir(anchors_dir):
        print("No anchors directory found")
        return

    term = term.lower()
    found = False

    for file in sorted(os.listdir(anchors_dir)):
        path = os.path.join(anchors_dir, file)
        if not file.endswith(".json"):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            event = str(data.get("event", ""))
            date = str(data.get("date", data.get("timestamp", file)))

            if term in event.lower():
                print(f"{date} → {event}")
                found = True

        except Exception as e:
            print(f"{file} → ERROR: {e}")

    if not found:
        print(f'No anchors matched: "{term}"')


def health():
    print("=== AETHIEA HEALTH ===")
    print("ROOT:", AETHIEA)

    mount_ok = os.path.ismount("/mnt/h")
    print("MOUNT /mnt/h:", "OK" if mount_ok else "FAIL")

    root_ok = os.path.isdir(AETHIEA)
    print("ROOT EXISTS:", "OK" if root_ok else "FAIL")

    memory_files = [
        "DATA/MEMORY/SYSTEM/aethiea.json",
        "DATA/MEMORY/STATE/current.json",
        "DATA/MEMORY/SESSIONS/latest.json",
    ]

    for rel in memory_files:
        full = os.path.join(AETHIEA, rel)
        print(f"MEMORY {rel}:", "OK" if os.path.isfile(full) else "FAIL")

    toolio_aeth = os.path.join(AETHIEA, "TOOLIO", "aeth")
    print("TOOLIO aeth:", "OK" if os.path.isfile(toolio_aeth) else "FAIL")

    local_tools = [
        os.path.join(HOME, ".local", "bin", "aeth-up"),
        os.path.join(HOME, ".local", "bin", "aeth-down"),
        os.path.join(HOME, ".local", "bin", "aeth-status"),
    ]
    for tool in local_tools:
        print(f"LOCAL TOOL {os.path.basename(tool)}:", "OK" if os.path.isfile(tool) else "FAIL")

    ollama_root = os.path.join(AETHIEA, "DATA", "OLLAMA", "blobs")
    partials = []
    if os.path.isdir(ollama_root):
        partials = sorted([f for f in os.listdir(ollama_root) if "partial" in f])
        print("OLLAMA BLOBS:", "OK")
        print("OLLAMA PARTIALS:", len(partials))
    else:
        print("OLLAMA BLOBS: FAIL")

    try:
        result = subprocess.run(
            ["pgrep", "-af", "ollama serve"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            print("OLLAMA RUNNING: YES")
        else:
            print("OLLAMA RUNNING: NO")
    except Exception:
        print("OLLAMA RUNNING: UNKNOWN")

    print("=== END HEALTH ===")


def route_cmd(cmd_input):
    try:
        from router import route_command
    except Exception as e:
        print("ROUTER IMPORT FAIL:", e)
        return

    result = route_command(cmd_input)

    print("=== ROUTE ===")
    print("INPUT:", cmd_input)

    if isinstance(result, dict):
        for k, v in result.items():
            print(f"{k.upper()}: {v}")
    else:
        print("RESULT:", result)

    print("=== END ROUTE ===")


def memory_read(name):
    target_map = {
        "system": "DATA/MEMORY/SYSTEM/aethiea.json",
        "state": "DATA/MEMORY/STATE/current.json",
        "session": "DATA/MEMORY/SESSIONS/latest.json",
        "nodes": "DATA/MEMORY/NODES/nodes.json",
        "routes": "DATA/MEMORY/ROUTES/routes.json",
        "layer_map": "DATA/MEMORY/ROUTES/layer_map.json",
        "domain_gcr_execution_map": "DATA/MEMORY/ROUTES/domain_gcr_execution_map.json",
    }

    if name == "hosts":
        hosts_dir = os.path.join(AETHIEA, "DATA", "MEMORY", "HOSTS")
        if not os.path.isdir(hosts_dir):
            print("No hosts directory found")
            return
        print("=== MEMORY HOSTS ===")
        for file in sorted(os.listdir(hosts_dir)):
            if not file.endswith(".json"):
                continue
            full = os.path.join(hosts_dir, file)
            try:
                with open(full, "r", encoding="utf-8") as f:
                    data = json.load(f)
                print(f"[{file}]")
                print(json.dumps(data, indent=2))
            except Exception as e:
                print(f"{file} → ERROR: {e}")
        print("=== END MEMORY HOSTS ===")
        return

    if name == "anchors" or name == "anchor":
        anchors_dir = os.path.join(AETHIEA, "DATA", "MEMORY", "ANCHORS")
        if not os.path.isdir(anchors_dir):
            print("No anchors directory found")
            return
        print("=== MEMORY ANCHORS ===")
        for file in sorted(os.listdir(anchors_dir)):
            if not file.endswith(".json"):
                continue
            full = os.path.join(anchors_dir, file)
            try:
                with open(full, "r", encoding="utf-8") as f:
                    data = json.load(f)
                print(f"[{file}]")
                print(json.dumps(data, indent=2))
            except Exception as e:
                print(f"{file} → ERROR: {e}")
        print("=== END MEMORY ANCHORS ===")
        return

    rel_path = target_map.get(name)
    if not rel_path:
        print("usage: aeth memory read <system|state|session|nodes|routes|layer_map|domain_gcr_execution_map|hosts|anchors>")
        return

    try:
        data = load(rel_path)
        print(f"=== MEMORY {name.upper()} ===")
        print(json.dumps(data, indent=2))
        print(f"=== END MEMORY {name.upper()} ===")
    except Exception as e:
        print(f"MEMORY READ FAIL ({name}): {e}")


def bae_call(bae_id):
    bae_path = os.path.join(AETHIEA, "MODS", "B43-RU5", bae_id)

    if not os.path.isdir(bae_path):
        print(f"BÆ:{bae_id} not found")
        return

    config_path = os.path.join(bae_path, "config.json")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        print("=== BÆ INVOKE ===")
        print("ID:", cfg.get("call_sign"))
        print("NAME:", cfg.get("name"))
        print("ROLE:", cfg.get("role"))
        print("TITLE:", cfg.get("title"))
        print("FUNCTION:", ", ".join(cfg.get("function", [])))
        print("STATE:", cfg.get("state"))
        print("=== END ===")

    except Exception as e:
        print("ERROR:", e)


def audit_file(target):
    path = target
    if not os.path.isabs(path):
        path = os.path.join(AETHIEA, target)

    print("=== AUDIT FILE ===")
    print("TARGET:", target)
    print("PATH:", path)

    if not os.path.exists(path):
        print("EXISTS: FAIL")
        print("=== END AUDIT FILE ===")
        return

    print("EXISTS: OK")
    print("READABLE:", "OK" if os.access(path, os.R_OK) else "FAIL")
    print("SIZE:", os.path.getsize(path), "bytes")

    if os.path.isdir(path):
        print("TYPE: directory")
        print("ITEMS:", len(os.listdir(path)))
        print("=== END AUDIT FILE ===")
        return

    ext = os.path.splitext(path)[1].lower()

    if ext == ".json":
        print("TYPE: json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                json.load(f)
            print("JSON: OK")
        except Exception as e:
            print("JSON: FAIL")
            print("ERROR:", e)

    elif ext == ".py":
        print("TYPE: python")
        result = subprocess.run(
            ["python3", "-m", "py_compile", path],
            capture_output=True,
            text=True
        )
        print("PYTHON SYNTAX:", "OK" if result.returncode == 0 else "FAIL")
        if result.stderr.strip():
            print(result.stderr.strip())

    elif ext in [".sh", ".bash"]:
        print("TYPE: shell/executable")
        first = ""
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                first = f.readline().strip()
        except Exception:
            pass

        print("SHEBANG:", first if first.startswith("#!") else "MISSING")

        if "bash" in first or "sh" in first or ext in [".sh", ".bash"]:
            result = subprocess.run(
                ["bash", "-n", path],
                capture_output=True,
                text=True
            )
            print("BASH SYNTAX:", "OK" if result.returncode == 0 else "FAIL")
            if result.stderr.strip():
                print(result.stderr.strip())

    elif ext in [".md", ".txt", ".log"]:
        print("TYPE:", ext.replace(".", "text/"))
        if os.path.getsize(path) > 0:
            print("CONTENT: OK")
        else:
            print("CONTENT: EMPTY")

    else:
        print("TYPE: unknown")
        print("PARSE: skipped")

    print("=== END AUDIT FILE ===")



def audit_system():
    print("=== AUDIT SYSTEM ===")

    required = ["CORE", "DATA", "DOMAINS", "LAYERS", "LOGS", "MODS", "TEMP", "TOOLIO", "GCR"]
    for d in required:
        full = os.path.join(AETHIEA, d)
        print(("OK: " if os.path.isdir(full) else "MISSING: ") + d)

    print("--- HEALTH ---")
    health()
    print("=== END AUDIT SYSTEM ===")


def audit_domains():
    print("=== AUDIT DOMAINS ===")
    root = os.path.join(AETHIEA, "DOMAINS")

    if not os.path.isdir(root):
        print("DOMAINS: MISSING")
        return

    for name in sorted(os.listdir(root)):
        full = os.path.join(root, name)
        if os.path.isdir(full):
            print("DOMAIN:", name)

    print("=== END AUDIT DOMAINS ===")


def audit_domain(name):
    print("=== AUDIT DOMAIN ===")
    print("DOMAIN:", name)

    path = os.path.join(AETHIEA, "DOMAINS", name)

    if not os.path.isdir(path):
        print("EXISTS: FAIL")
        print("PATH:", path)
        return

    print("EXISTS: OK")
    print("PATH:", path)

    for item in sorted(os.listdir(path)):
        full = os.path.join(path, item)
        if os.path.isdir(full):
            mapping = os.path.join(full, "MAPPING.json")
            print(f"ENTITY: {item}")
            print("  MAPPING:", "OK" if os.path.isfile(mapping) else "MISSING")

    print("=== END AUDIT DOMAIN ===")

def universal_dispatch(args):
    if not args:
        return False

    verb = args[0].lower()
    scope = args[1].lower() if len(args) > 1 else None

    if verb == "status" and scope == "system":
        health()
        return True

    if verb == "invoke" and scope == "bae":
        if len(args) < 3:
            print("usage: aeth invoke bae <id>")
            return True
        bae_call(args[2])
        return True

    if verb == "read" and scope == "memory":
        if len(args) < 3:
            print("usage: aeth read memory <state|session|system|nodes|routes|hosts|anchors>")
            return True
        memory_read(args[2])
        return True

    if verb == "audit" and (scope is None or scope == "system"):
        audit_system()
        return True

    if verb == "audit" and scope == "domains":
        audit_domains()
        return True

    if verb == "audit" and scope == "domain":
        if len(args) < 3:
            print("usage: aeth audit domain <name>")
            return True
        audit_domain(" ".join(args[2:]))
        return True

    if verb == "audit" and scope == "file":
        if len(args) < 3:
            print("usage: aeth audit file <path>")
            return True
        audit_file(" ".join(args[2:]))
        return True

    return False


def execute_entity(value):
    if "/" not in value:
        print("usage: aeth execute entity <DOMAIN/ENTITY>")
        return

    domain, entity = value.split("/", 1)
    entity_path = os.path.join(AETHIEA, "DOMAINS", domain.strip().upper(), entity.strip())
    binding_file = os.path.join(entity_path, "BINDING.json")

    print("=== EXECUTE ENTITY ===")
    print("INPUT:", value)

    if not os.path.isdir(entity_path):
        print("STATUS: denied")
        print("REASON: entity_not_found")
        print("=== END EXECUTE ENTITY ===")
        return

    if not os.path.isfile(binding_file):
        print("STATUS: denied")
        print("REASON: binding_missing")
        print("=== END EXECUTE ENTITY ===")
        return

    with open(binding_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    hook = data.get("execution_hook", "")
    mode = data.get("execution_mode", "")
    gcr = data.get("gcr_zone", [])
    domain_value = str(data.get("domain", domain.strip().upper())).upper()
    not_allowed = data.get("not_allowed", [])

    if domain_value == "PRIVATE" or "VAULT_ONLY" in gcr:
        print("ENTITY:", data.get("entity", entity.strip()))
        print("DOMAIN:", domain_value)
        print("GCR_ZONE:", gcr)
        print("STATUS: denied")
        print("REASON: private_execution_denied")
        log_event(f"DENY private_execution entity={value}")
        print("=== END EXECUTE ENTITY ===")
        return

    print("ENTITY:", data.get("entity", entity.strip()))
    print("DOMAIN:", data.get("domain", domain.strip().upper()))
    print("GCR_ZONE:", gcr)
    print("EXECUTION_MODE:", mode)
    print("EXECUTION_HOOK:", hook)

    if not hook:
        print("STATUS: denied")
        print("REASON: no_execution_hook")
        print("=== END EXECUTE ENTITY ===")
        return

    hook_path = os.path.join(AETHIEA, hook)

    if not os.path.isfile(hook_path):
        print("STATUS: denied")
        print("REASON: hook_missing")
        print("HOOK_PATH:", hook_path)
        print("=== END EXECUTE ENTITY ===")
        return

    result = subprocess.run([hook_path], capture_output=True, text=True)

    print("HOOK_RETURN:", result.returncode)
    if result.stdout.strip():
        print("STDOUT:", result.stdout.strip())
    if result.stderr.strip():
        print("STDERR:", result.stderr.strip())

    log_event(f"EXECUTE entity={value} hook={hook} return={result.returncode}")

    print("STATUS:", "executed" if result.returncode == 0 else "failed")
    print("=== END EXECUTE ENTITY ===")


def report_safety():
    report_path = os.path.join(AETHIEA, "EXECUTION", "REPORTS", "security.log")

    print("=== SAFETY REPORT ===")
    print("PATH:", report_path)

    if not os.path.isfile(report_path):
        print("STATUS: no_report")
        print("=== END SAFETY REPORT ===")
        return

    with open(report_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.rstrip() for line in f.readlines() if line.strip()]

    if not lines:
        print("STATUS: empty")
        print("=== END SAFETY REPORT ===")
        return

    print("STATUS: active")
    print("ENTRIES:", len(lines))
    print("--- LAST 20 ---")
    for line in lines[-20:]:
        print(line)

    print("=== END SAFETY REPORT ===")

def report_pipelines():
    base = os.path.join(AETHIEA, "EXECUTION", "PIPELINES")

    print("=== PIPELINE REPORT ===")

    if not os.path.isdir(base):
        print("STATUS: no_pipelines_directory")
        print("=== END PIPELINE REPORT ===")
        return

    for pipe in sorted(os.listdir(base)):
        pdir = os.path.join(base, pipe)
        if not os.path.isdir(pdir):
            continue

        log = os.path.join(pdir, "LOGS", "pipeline.log")

        print(f"\nPIPELINE: {pipe}")

        if not os.path.isfile(log):
            print("  STATUS: no_log")
            continue

        with open(log, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        total = len(lines)
        processed = sum(1 for line in lines if "| PROCESS |" in line)
        rejected = sum(1 for line in lines if "| REJECT |" in line)

        print(f"  TOTAL EVENTS: {total}")
        print(f"  PROCESSED: {processed}")
        print(f"  REJECTED: {rejected}")

        if total:
            print(f"  SUCCESS RATE: {round((processed / total) * 100, 2)}%")
        else:
            print("  SUCCESS RATE: n/a")

    print("\n=== END PIPELINE REPORT ===")

def hud_ae1of1():
    pipe_root = os.path.join(AETHIEA, "EXECUTION", "PIPELINES")
    sec_path = os.path.join(AETHIEA, "EXECUTION", "REPORTS", "security.log")
    state_path = os.path.join(AETHIEA, "DATA", "MEMORY", "STATE", "current.json")
    session_path = os.path.join(AETHIEA, "DATA", "MEMORY", "SESSIONS", "latest.json")

    print("=== AE1OF1 HUD ===")

    try:
        state = load(os.path.relpath(state_path, AETHIEA))
        print("SYSTEM:", state.get("status", "unknown"))
        print("PHASE:", state.get("phase", "unknown"))
        print("HOST:", state.get("active_host", "unknown"))
    except Exception:
        print("SYSTEM: unknown")

    try:
        session = load(os.path.relpath(session_path, AETHIEA))
        print("NEXT:", session.get("resume_next", "unknown"))
    except Exception:
        print("NEXT: unknown")

    active = processed = rejected = 0

    if os.path.isdir(pipe_root):
        for pipe in sorted(os.listdir(pipe_root)):
            p = os.path.join(pipe_root, pipe)
            if not os.path.isdir(p):
                continue
            active += 1
            log_path = os.path.join(p, "LOGS", "pipeline.log")
            if os.path.isfile(log_path):
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    processed += sum(1 for l in lines if "OUTPUT" in l)
                    rejected += sum(1 for l in lines if "REJECT" in l)

    sec_entries = 0
    last_security = "none"
    if os.path.isfile(sec_path):
        with open(sec_path, "r", encoding="utf-8", errors="ignore") as f:
            sec_lines = [x.strip() for x in f.readlines() if x.strip()]
            sec_entries = len(sec_lines)
            if sec_lines:
                last_security = sec_lines[-1]

    print("PIPELINES:", active)
    print("PROCESSED:", processed)
    print("REJECTED:", rejected)
    print("SECURITY_EVENTS:", sec_entries)
    print("PRIVATE:", "protected")
    print("LAST_SECURITY:", last_security)
    print("=== END AE1OF1 HUD ===")


def report_all():
    print("=== SYSTEM STATUS ===")
    status()
    print()

    report_health()
    print()

    report_memory()
    print()

    report_domains()
    print()

    report_execution()
    print()

    report_mods()
    print()

    print("=== PIPELINES ===")
    report_pipelines()
    print()

    report_rejects()
    print()

    report_reject_classes()
    print()

    report_reject_reasons()
    print()

    report_pending()
    print()

    report_latest()
    print()

    report_pipeline_health()
    print()

    report_cleanup()
    print()

    print("=== SECURITY ===")
    report_safety()
    print()

    print("=== HUD ===")
    hud_ae1of1()
def snapshot():
    import datetime
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
    out_dir = os.path.join(AETHIEA, "DATA", "MEMORY", "SNAPSHOTS")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"snapshot_{ts}.txt")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("=== AETHIEA SNAPSHOT ===\n")
        f.write(f"TIME_UTC: {ts}\n")
        f.write(f"ROOT: {AETHIEA}\n\n")
        f.write("=== DIRECTORIES ===\n")
        for root, dirs, files in os.walk(AETHIEA):
            f.write(root + "\n")
        f.write("\n=== FILES ===\n")
        for root, dirs, files in os.walk(AETHIEA):
            for name in files:
                f.write(os.path.join(root, name) + "\n")

    print("SNAPSHOT:", out_file)

def map_system():
    print("=== AETHIEA MAP ===")
    print("ROOT:", AETHIEA)
    print()

    sections = [
        ("CORE", "CORE"),
        ("LAYERS", "LAYERS"),
        ("DOMAINS", "DOMAINS"),
        ("EXECUTION", "EXECUTION"),
        ("MEMORY", "DATA/MEMORY"),
        ("MODS", "MODS"),
        ("GCR", "GCR"),
    ]

    for label, rel in sections:
        path = os.path.join(AETHIEA, rel)
        print(f"=== {label} ===")
        if os.path.isdir(path):
            for name in sorted(os.listdir(path)):
                print("-", name)
        else:
            print("MISSING:", path)
        print()


def _count_files(path):
    if not os.path.isdir(path):
        return 0
    total = 0
    for _, _, files in os.walk(path):
        total += len(files)
    return total

def _latest_file(path):
    if not os.path.isdir(path):
        return "none"
    files = []
    for root, _, names in os.walk(path):
        for name in names:
            full = os.path.join(root, name)
            try:
                files.append((os.path.getmtime(full), full))
            except OSError:
                pass
    if not files:
        return "none"
    return max(files)[1]

def report_memory():
    print("=== MEMORY REPORT ===")
    base = os.path.join(AETHIEA, "DATA", "MEMORY")
    sections = ["ANCHORS", "HOSTS", "NODES", "ROUTES", "SESSIONS", "SNAPSHOTS", "STATE", "SYSTEM"]
    for sec in sections:
        path = os.path.join(base, sec)
        print(f"{sec}: files={_count_files(path)} latest={_latest_file(path)}")
    print("=== END MEMORY REPORT ===")

def report_domains():
    print("=== DOMAIN REPORT ===")
    base = os.path.join(AETHIEA, "DOMAINS")
    for lane in ["FOR PROFIT", "NONPROFIT", "PRIVATE"]:
        path = os.path.join(base, lane)
        print(f"\n{lane}:")
        if not os.path.isdir(path):
            print("  STATUS: missing")
            continue
        for name in sorted(os.listdir(path)):
            full = os.path.join(path, name)
            if os.path.isdir(full):
                mapping = os.path.isfile(os.path.join(full, "MAPPING.json"))
                binding = os.path.isfile(os.path.join(full, "BINDING.json"))
                print(f"  - {name} | mapping={mapping} binding={binding}")
    print("=== END DOMAIN REPORT ===")

def report_execution():
    print("=== EXECUTION REPORT ===")
    base = os.path.join(AETHIEA, "EXECUTION")
    sections = ["PIPELINES", "REPORTS", "RUNTIME", "OUTPUT", "JOBS", "EXPORTS"]
    for sec in sections:
        path = os.path.join(base, sec)
        print(f"{sec}: files={_count_files(path)} latest={_latest_file(path)}")
    print("=== END EXECUTION REPORT ===")

def report_mods():
    print("=== MODS REPORT ===")
    base = os.path.join(AETHIEA, "MODS")
    if not os.path.isdir(base):
        print("STATUS: missing")
        return
    for mod in sorted(os.listdir(base)):
        path = os.path.join(base, mod)
        if os.path.isdir(path):
            print(f"{mod}: files={_count_files(path)} latest={_latest_file(path)}")
    print("=== END MODS REPORT ===")

def report_rejects():
    print("=== REJECT REPORT ===")
    pbase = os.path.join(AETHIEA, "EXECUTION", "PIPELINES")
    if not os.path.isdir(pbase):
        print("STATUS: no_pipelines_directory")
        return

    total_rejected = 0
    for pipe in sorted(os.listdir(pbase)):
        pdir = os.path.join(pbase, pipe)
        if not os.path.isdir(pdir):
            continue

        rejected_dir = os.path.join(pdir, "REJECTED")
        process_dir = os.path.join(pdir, "PROCESS")

        rejected_count = _count_files(rejected_dir)
        rejected_sources = 0
        if os.path.isdir(process_dir):
            for name in os.listdir(process_dir):
                if ".rejected.source." in name:
                    rejected_sources += 1

        total_rejected += rejected_count
        latest = _latest_file(rejected_dir)

        print(f"\nPIPELINE: {pipe}")
        print(f"  REJECTED: {rejected_count}")
        print(f"  REJECTED_SOURCES: {rejected_sources}")
        print(f"  LATEST_REJECTED: {latest}")

    print(f"\nTOTAL_REJECTED: {total_rejected}")
    print("=== END REJECT REPORT ===")

def report_health():
    print("=== HEALTH SUMMARY ===")
    print("ROOT:", AETHIEA)
    print("CORE:", "ok" if os.path.isfile(os.path.join(AETHIEA, "CORE", "aeth.py")) else "missing")
    print("TOOLIO:", "ok" if os.path.isfile(os.path.join(AETHIEA, "TOOLIO", "aeth")) else "missing")
    print("MEMORY:", "ok" if os.path.isdir(os.path.join(AETHIEA, "DATA", "MEMORY")) else "missing")
    print("PIPELINES:", "ok" if os.path.isdir(os.path.join(AETHIEA, "EXECUTION", "PIPELINES")) else "missing")
    print("SECURITY_LOG:", "ok" if os.path.isfile(os.path.join(AETHIEA, "EXECUTION", "REPORTS", "security.log")) else "missing")
    print("SNAPSHOTS:", _count_files(os.path.join(AETHIEA, "DATA", "MEMORY", "SNAPSHOTS")))
    print("=== END HEALTH SUMMARY ===")


def _classify_reject_file(path):
    name = os.path.basename(path).lower()
    text = ""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read().lower()
    except Exception:
        pass

    blob = name + " " + text

    if "security" in blob or "action_not_allowed" in blob or "private" in blob:
        return "security"
    if "validation" in blob or "invalid" in blob or "missing" in blob:
        return "validation"
    if "route" in blob or "routing" in blob or "domain" in blob:
        return "routing"
    return "unknown"

def report_reject_classes():
    print("=== REJECT CLASSIFICATION REPORT ===")
    pbase = os.path.join(AETHIEA, "EXECUTION", "PIPELINES")
    classes_total = {"security": 0, "validation": 0, "routing": 0, "unknown": 0}

    if not os.path.isdir(pbase):
        print("STATUS: no_pipelines_directory")
        return

    for pipe in sorted(os.listdir(pbase)):
        pdir = os.path.join(pbase, pipe)
        if not os.path.isdir(pdir):
            continue

        rejected_dir = os.path.join(pdir, "REJECTED")
        local = {"security": 0, "validation": 0, "routing": 0, "unknown": 0}

        if os.path.isdir(rejected_dir):
            for root, _, files in os.walk(rejected_dir):
                for name in files:
                    full = os.path.join(root, name)
                    cls = _classify_reject_file(full)
                    local[cls] += 1
                    classes_total[cls] += 1

        print(f"\nPIPELINE: {pipe}")
        for k in ["security", "validation", "routing", "unknown"]:
            print(f"  {k.upper()}: {local[k]}")

    print("\nTOTALS:")
    for k in ["security", "validation", "routing", "unknown"]:
        print(f"  {k.upper()}: {classes_total[k]}")
    print("=== END REJECT CLASSIFICATION REPORT ===")

def report_pending():
    print("=== PENDING JOB REPORT ===")
    pbase = os.path.join(AETHIEA, "EXECUTION", "PIPELINES")

    if not os.path.isdir(pbase):
        print("STATUS: no_pipelines_directory")
        return

    for pipe in sorted(os.listdir(pbase)):
        pdir = os.path.join(pbase, pipe)
        if not os.path.isdir(pdir):
            continue

        input_dir = os.path.join(pdir, "INPUT")
        process_dir = os.path.join(pdir, "PROCESS")

        input_files = _count_files(input_dir)
        process_files = 0
        active_process_files = 0

        if os.path.isdir(process_dir):
            for root, _, files in os.walk(process_dir):
                for name in files:
                    process_files += 1
                    if not name.endswith(".done.json") and ".rejected." not in name:
                        active_process_files += 1

        print(f"\nPIPELINE: {pipe}")
        print(f"  INPUT_PENDING: {input_files}")
        print(f"  PROCESS_TOTAL: {process_files}")
        print(f"  PROCESS_ACTIVE: {active_process_files}")

    print("=== END PENDING JOB REPORT ===")

def report_latest():
    print("=== LATEST PIPELINE FILES ===")
    pbase = os.path.join(AETHIEA, "EXECUTION", "PIPELINES")

    if not os.path.isdir(pbase):
        print("STATUS: no_pipelines_directory")
        return

    for pipe in sorted(os.listdir(pbase)):
        pdir = os.path.join(pbase, pipe)
        if not os.path.isdir(pdir):
            continue

        print(f"\nPIPELINE: {pipe}")
        print("  LATEST_INPUT:", _latest_file(os.path.join(pdir, "INPUT")))
        print("  LATEST_PROCESS:", _latest_file(os.path.join(pdir, "PROCESS")))
        print("  LATEST_OUTPUT:", _latest_file(os.path.join(pdir, "OUTPUT")))
        print("  LATEST_REJECTED:", _latest_file(os.path.join(pdir, "REJECTED")))

    print("=== END LATEST PIPELINE FILES ===")


def _pipeline_metrics(pipe):
    pdir = os.path.join(AETHIEA, "EXECUTION", "PIPELINES", pipe)
    log_path = os.path.join(pdir, "LOGS", "pipeline.log")
    input_dir = os.path.join(pdir, "INPUT")
    process_dir = os.path.join(pdir, "PROCESS")
    output_dir = os.path.join(pdir, "OUTPUT")
    rejected_dir = os.path.join(pdir, "REJECTED")

    total_events = 0
    processed = 0
    rejected_events = 0

    if os.path.isfile(log_path):
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = [x.strip() for x in f.readlines() if x.strip()]
        total_events = len(lines)
        processed = sum(1 for x in lines if "PROCESSED" in x.upper())
        rejected_events = sum(1 for x in lines if "REJECT" in x.upper())

    input_pending = _count_files(input_dir)
    output_files = _count_files(output_dir)
    rejected_files = _count_files(rejected_dir)

    process_total = 0
    process_active = 0
    if os.path.isdir(process_dir):
        for name in os.listdir(process_dir):
            fp = os.path.join(process_dir, name)
            if not os.path.isfile(fp):
                continue
            process_total += 1
            if not name.endswith(".done.json") and ".rejected." not in name:
                process_active += 1

    success_rate = 0.0
    if total_events:
        success_rate = round((processed / total_events) * 100, 2)

    return {
        "pipe": pipe,
        "total_events": total_events,
        "processed": processed,
        "rejected_events": rejected_events,
        "rejected_files": rejected_files,
        "input_pending": input_pending,
        "process_total": process_total,
        "process_active": process_active,
        "output_files": output_files,
        "success_rate": success_rate,
        "latest_output": _latest_file(output_dir),
        "latest_rejected": _latest_file(rejected_dir),
    }

def _score_pipeline(m):
    flags = []

    if m["total_events"] == 0:
        flags.append("NO_EVENTS")

    if m["rejected_files"] >= 3 or m["rejected_events"] >= 3:
        flags.append("HIGH_REJECTION_PRESSURE")

    if m["process_active"] >= 4:
        flags.append("ACTIVE_PROCESS_PRESSURE")

    if m["input_pending"] >= 1:
        flags.append("INPUT_PENDING")

    if m["total_events"] >= 5 and m["success_rate"] < 15:
        flags.append("LOW_SUCCESS_RATE")

    if m["latest_output"] == "none" and (m["process_active"] > 0 or m["input_pending"] > 0):
        flags.append("NO_OUTPUT_WITH_ACTIVE_WORK")

    if "HIGH_REJECTION_PRESSURE" in flags and "LOW_SUCCESS_RATE" in flags:
        status = "CRITICAL"
    elif flags:
        status = "DEGRADED"
    else:
        status = "HEALTHY"

    return status, flags

def report_pipeline_health():
    print("=== PIPELINE HEALTH REPORT ===")
    pbase = os.path.join(AETHIEA, "EXECUTION", "PIPELINES")

    if not os.path.isdir(pbase):
        print("STATUS: no_pipelines_directory")
        return

    system_flags = 0
    for pipe in sorted(os.listdir(pbase)):
        pdir = os.path.join(pbase, pipe)
        if not os.path.isdir(pdir):
            continue

        m = _pipeline_metrics(pipe)
        status, flags = _score_pipeline(m)
        system_flags += len(flags)

        print(f"\nPIPELINE: {pipe}")
        print(f"  STATUS: {status}")
        print(f"  SUCCESS_RATE: {m['success_rate']}%")
        print(f"  EVENTS: {m['total_events']}")
        print(f"  PROCESSED: {m['processed']}")
        print(f"  REJECTED_EVENTS: {m['rejected_events']}")
        print(f"  REJECTED_FILES: {m['rejected_files']}")
        print(f"  INPUT_PENDING: {m['input_pending']}")
        print(f"  PROCESS_ACTIVE: {m['process_active']}")
        print(f"  FLAGS: {', '.join(flags) if flags else 'none'}")

    print(f"\nSYSTEM_FLAGS: {system_flags}")
    if system_flags == 0:
        print("SYSTEM_PIPELINE_STATUS: HEALTHY")
    elif system_flags < 5:
        print("SYSTEM_PIPELINE_STATUS: DEGRADED")
    else:
        print("SYSTEM_PIPELINE_STATUS: CRITICAL")

    print("=== END PIPELINE HEALTH REPORT ===")


def _reject_reason(path):
    name = os.path.basename(path).lower()
    text = ""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read().lower()
    except Exception:
        pass

    blob = name + " " + text

    checks = [
        ("action_not_allowed", "ACTION_NOT_ALLOWED"),
        ("private", "PRIVATE_BOUNDARY"),
        ("security", "SECURITY_POLICY"),
        ("validation", "VALIDATION_FAILURE"),
        ("invalid", "INVALID_INPUT"),
        ("missing", "MISSING_REQUIRED_FIELD"),
        ("route", "ROUTING_FAILURE"),
        ("routing", "ROUTING_FAILURE"),
        ("domain", "DOMAIN_MISMATCH"),
    ]

    for needle, reason in checks:
        if needle in blob:
            return reason

    return "UNCLASSIFIED_REASON"

def report_reject_reasons():
    print("=== REJECT REASON REPORT ===")
    pbase = os.path.join(AETHIEA, "EXECUTION", "PIPELINES")

    if not os.path.isdir(pbase):
        print("STATUS: no_pipelines_directory")
        return

    system_reasons = {}

    for pipe in sorted(os.listdir(pbase)):
        pdir = os.path.join(pbase, pipe)
        if not os.path.isdir(pdir):
            continue

        rejected_dir = os.path.join(pdir, "REJECTED")
        local = {}

        if os.path.isdir(rejected_dir):
            for root, _, files in os.walk(rejected_dir):
                for name in files:
                    full = os.path.join(root, name)
                    reason = _reject_reason(full)
                    local[reason] = local.get(reason, 0) + 1
                    system_reasons[reason] = system_reasons.get(reason, 0) + 1

        print(f"\nPIPELINE: {pipe}")
        if local:
            for reason, count in sorted(local.items()):
                print(f"  {reason}: {count}")
        else:
            print("  none")

    print("\nSYSTEM REASONS:")
    if system_reasons:
        for reason, count in sorted(system_reasons.items()):
            print(f"  {reason}: {count}")
    else:
        print("  none")

    print("=== END REJECT REASON REPORT ===")


def _retry_class(reason):
    retryable = {
        "VALIDATION_FAILURE",
        "MISSING_REQUIRED_FIELD",
        "ROUTING_FAILURE"
    }

    permanent = {
        "PRIVATE_BOUNDARY",
        "SECURITY_POLICY",
        "ACTION_NOT_ALLOWED"
    }

    if reason in retryable:
        return "RETRYABLE"
    if reason in permanent:
        return "PERMANENT"
    return "UNKNOWN"

def report_retry_matrix():
    print("=== RETRY MATRIX ===")

    pbase = os.path.join(AETHIEA, "EXECUTION", "PIPELINES")

    if not os.path.isdir(pbase):
        print("STATUS: no_pipelines_directory")
        return

    for pipe in sorted(os.listdir(pbase)):
        pdir = os.path.join(pbase, pipe)
        if not os.path.isdir(pdir):
            continue

        rejected_dir = os.path.join(pdir, "REJECTED")

        retry = 0
        permanent = 0
        unknown = 0

        if os.path.isdir(rejected_dir):
            for root, _, files in os.walk(rejected_dir):
                for name in files:
                    full = os.path.join(root, name)
                    reason = _reject_reason(full)
                    classification = _retry_class(reason)

                    if classification == "RETRYABLE":
                        retry += 1
                    elif classification == "PERMANENT":
                        permanent += 1
                    else:
                        unknown += 1

        print(f"\nPIPELINE: {pipe}")
        print(f"  RETRYABLE: {retry}")
        print(f"  PERMANENT: {permanent}")
        print(f"  UNKNOWN: {unknown}")

    print("\n=== END RETRY MATRIX ===")


def build_latest_report_data():
    import datetime

    report = {
        "generated_utc": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": AETHIEA,
        "system": {},
        "pipelines": {},
        "summary": {
            "pipeline_count": 0,
            "system_flags": 0,
            "system_pipeline_status": "UNKNOWN"
        }
    }

    try:
        state = load("DATA/MEMORY/STATE/current.json")
        report["system"] = state
    except Exception:
        report["system"] = {"status": "unknown"}

    pbase = os.path.join(AETHIEA, "EXECUTION", "PIPELINES")
    if os.path.isdir(pbase):
        for pipe in sorted(os.listdir(pbase)):
            pdir = os.path.join(pbase, pipe)
            if not os.path.isdir(pdir):
                continue

            m = _pipeline_metrics(pipe)
            status, flags = _score_pipeline(m)

            report["pipelines"][pipe] = {
                "status": status,
                "flags": flags,
                "metrics": m
            }

        report["summary"]["pipeline_count"] = len(report["pipelines"])
        report["summary"]["system_flags"] = sum(len(v["flags"]) for v in report["pipelines"].values())

        if report["summary"]["system_flags"] == 0:
            report["summary"]["system_pipeline_status"] = "HEALTHY"
        elif report["summary"]["system_flags"] < 5:
            report["summary"]["system_pipeline_status"] = "DEGRADED"
        else:
            report["summary"]["system_pipeline_status"] = "CRITICAL"

    return report

def export_latest_report():
    import json

    out_dir = os.path.join(AETHIEA, "EXECUTION", "REPORTS")
    os.makedirs(out_dir, exist_ok=True)

    data = build_latest_report_data()

    json_path = os.path.join(out_dir, "latest_report.json")
    txt_path = os.path.join(out_dir, "latest_report.txt")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=== AETHIEA LATEST REPORT ===\n")
        f.write(f"GENERATED_UTC: {data.get('generated_utc')}\n")
        f.write(f"ROOT: {data.get('root')}\n")
        f.write(f"SYSTEM_STATUS: {data.get('system', {}).get('status', 'unknown')}\n")
        f.write(f"PIPELINES: {data['summary']['pipeline_count']}\n")
        f.write(f"SYSTEM_FLAGS: {data['summary']['system_flags']}\n")
        f.write(f"SYSTEM_PIPELINE_STATUS: {data['summary']['system_pipeline_status']}\n\n")

        for pipe, pdata in data["pipelines"].items():
            m = pdata["metrics"]
            f.write(f"PIPELINE: {pipe}\n")
            f.write(f"  STATUS: {pdata['status']}\n")
            f.write(f"  FLAGS: {', '.join(pdata['flags']) if pdata['flags'] else 'none'}\n")
            f.write(f"  SUCCESS_RATE: {m['success_rate']}%\n")
            f.write(f"  EVENTS: {m['total_events']}\n")
            f.write(f"  PROCESSED: {m['processed']}\n")
            f.write(f"  REJECTED_EVENTS: {m['rejected_events']}\n")
            f.write(f"  REJECTED_FILES: {m['rejected_files']}\n")
            f.write(f"  INPUT_PENDING: {m['input_pending']}\n")
            f.write(f"  PROCESS_ACTIVE: {m['process_active']}\n\n")

    print("EXPORTED_JSON:", json_path)
    print("EXPORTED_TXT:", txt_path)


def hud_ae1of1_latest():
    import json

    report_path = os.path.join(AETHIEA, "EXECUTION", "REPORTS", "latest_report.json")

    if not os.path.isfile(report_path):
        print("=== AE1OF1 HUD ===")
        print("LATEST_REPORT: missing")
        print("FALLBACK: raw hud")
        hud_ae1of1()
        return

    with open(report_path, "r", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)

    system = data.get("system", {})
    summary = data.get("summary", {})
    pipelines = data.get("pipelines", {})

    print("=== AE1OF1 HUD ===")
    print("SOURCE: latest_report.json")
    print("GENERATED_UTC:", data.get("generated_utc", "unknown"))
    print("SYSTEM:", system.get("status", "unknown"))
    print("HOST:", system.get("active_host", "unknown"))
    print("PHASE:", system.get("phase", "unknown"))
    print("PIPELINES:", summary.get("pipeline_count", 0))
    print("SYSTEM_FLAGS:", summary.get("system_flags", 0))
    print("PIPELINE_STATUS:", summary.get("system_pipeline_status", "UNKNOWN"))

    critical = []
    degraded = []

    for name, pdata in pipelines.items():
        status = pdata.get("status", "UNKNOWN")
        if status == "CRITICAL":
            critical.append(name)
        elif status == "DEGRADED":
            degraded.append(name)

    print("CRITICAL:", ", ".join(critical) if critical else "none")
    print("DEGRADED:", ", ".join(degraded) if degraded else "none")

    print()
    print("=== PIPELINE SNAPSHOT ===")
    for name, pdata in pipelines.items():
        m = pdata.get("metrics", {})
        flags = pdata.get("flags", [])
        print(f"{name}: {pdata.get('status', 'UNKNOWN')} | success={m.get('success_rate', 0)}% | active={m.get('process_active', 0)} | flags={', '.join(flags) if flags else 'none'}")

    print("=== END AE1OF1 HUD ===")


def snapshot_lite():
    import datetime, json

    ts = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
    out_dir = os.path.join(AETHIEA, "DATA", "MEMORY", "SNAPSHOTS")
    os.makedirs(out_dir, exist_ok=True)

    out_file = os.path.join(out_dir, f"snapshot_lite_{ts}.txt")
    report_path = os.path.join(AETHIEA, "EXECUTION", "REPORTS", "latest_report.json")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("=== AETHIEA SNAPSHOT LITE ===\n")
        f.write(f"TIME_UTC: {ts}\n")
        f.write(f"ROOT: {AETHIEA}\n\n")

        f.write("=== TOP LEVEL ===\n")
        for name in sorted(os.listdir(AETHIEA)):
            f.write(f"- {name}\n")

        f.write("\n=== LATEST REPORT SUMMARY ===\n")
        if os.path.isfile(report_path):
            with open(report_path, "r", encoding="utf-8", errors="ignore") as rf:
                data = json.load(rf)
            f.write(f"SYSTEM_STATUS: {data.get('system', {}).get('status', 'unknown')}\n")
            f.write(f"PIPELINES: {data.get('summary', {}).get('pipeline_count', 0)}\n")
            f.write(f"SYSTEM_FLAGS: {data.get('summary', {}).get('system_flags', 0)}\n")
            f.write(f"PIPELINE_STATUS: {data.get('summary', {}).get('system_pipeline_status', 'UNKNOWN')}\n")
        else:
            f.write("latest_report.json: missing\n")

    print("SNAPSHOT_LITE:", out_file)

def snapshot_full():
    snapshot()


def snapshot_xofit():
    import datetime, os, json

    ts = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
    out_dir = os.path.join(AETHIEA, "DATA", "MEMORY", "SNAPSHOTS")
    os.makedirs(out_dir, exist_ok=True)

    out_file = os.path.join(out_dir, f"snapshot_xofit_{ts}.txt")

    mappings = {
        "B43-RU5_AGENT": {
            "X": ["config.json", "role.txt"],
            "O": ["rules.txt"],
            "FIT": ["README.md", "role.txt"]
        },
        "DOMAIN": {
            "X": ["BINDING.json", "MAPPING.json", "config.json"],
            "O": ["PIPELINE.sh", "routes.json"],
            "FIT": ["README.md", "index.html"]
        },
        "LAYER": {
            "X": ["MAPPING.json"],
            "O": ["MAPPING.json"],
            "FIT": ["README.md"]
        },
        "PIPELINE": {
            "X": ["CONFIG/pipeline.json"],
            "O": ["run.sh", "PROCESS", "VALIDATORS"],
            "FIT": ["LOGS/pipeline.log", "OUTPUT"]
        }
    }

    def exists_any(base, names):
        found = []
        for name in names:
            fp = os.path.join(base, name)
            if os.path.exists(fp):
                found.append(name)
        return found

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("=== AETHIEA X:O:FIT SNAPSHOT ===\n")
        f.write(f"TIME_UTC: {ts}\n")
        f.write(f"ROOT: {AETHIEA}\n\n")

        f.write("=== SCHEMA ===\n")
        f.write("X = SKELETON / structure / identity / configuration\n")
        f.write("O = MUSCLE / behavior / rules / execution logic\n")
        f.write("FIT = SKIN / interface / readable presentation / external mapping\n\n")

        f.write("=== B43-RU5 AGENTS ===\n")
        b43 = os.path.join(AETHIEA, "MODS", "B43-RU5")
        if os.path.isdir(b43):
            for name in sorted(os.listdir(b43)):
                ap = os.path.join(b43, name)
                if os.path.isdir(ap) and name.isdigit():
                    f.write(f"\n[{name}]\n")
                    f.write("X: " + str(exists_any(ap, mappings["B43-RU5_AGENT"]["X"])) + "\n")
                    f.write("O: " + str(exists_any(ap, mappings["B43-RU5_AGENT"]["O"])) + "\n")
                    f.write("FIT: " + str(exists_any(ap, mappings["B43-RU5_AGENT"]["FIT"])) + "\n")

        f.write("\n=== DOMAINS ===\n")
        domains = os.path.join(AETHIEA, "DOMAINS")
        if os.path.isdir(domains):
            for root, dirs, files in os.walk(domains):
                rel = os.path.relpath(root, domains)
                if rel == ".":
                    continue
                hits = (
                    exists_any(root, mappings["DOMAIN"]["X"]) +
                    exists_any(root, mappings["DOMAIN"]["O"]) +
                    exists_any(root, mappings["DOMAIN"]["FIT"])
                )
                if hits:
                    f.write(f"\n[{rel}]\n")
                    f.write("X: " + str(exists_any(root, mappings["DOMAIN"]["X"])) + "\n")
                    f.write("O: " + str(exists_any(root, mappings["DOMAIN"]["O"])) + "\n")
                    f.write("FIT: " + str(exists_any(root, mappings["DOMAIN"]["FIT"])) + "\n")

        f.write("\n=== LAYERS ===\n")
        layers = os.path.join(AETHIEA, "LAYERS")
        if os.path.isdir(layers):
            for name in sorted(os.listdir(layers)):
                lp = os.path.join(layers, name)
                if os.path.isdir(lp):
                    f.write(f"\n[{name}]\n")
                    f.write("X: " + str(exists_any(lp, mappings["LAYER"]["X"])) + "\n")
                    f.write("O: " + str(exists_any(lp, mappings["LAYER"]["O"])) + "\n")
                    f.write("FIT: " + str(exists_any(lp, mappings["LAYER"]["FIT"])) + "\n")

        f.write("\n=== PIPELINES ===\n")
        pipes = os.path.join(AETHIEA, "EXECUTION", "PIPELINES")
        if os.path.isdir(pipes):
            for name in sorted(os.listdir(pipes)):
                pp = os.path.join(pipes, name)
                if os.path.isdir(pp):
                    f.write(f"\n[{name}]\n")
                    f.write("X: " + str(exists_any(pp, mappings["PIPELINE"]["X"])) + "\n")
                    f.write("O: " + str(exists_any(pp, mappings["PIPELINE"]["O"])) + "\n")
                    f.write("FIT: " + str(exists_any(pp, mappings["PIPELINE"]["FIT"])) + "\n")

    print("SNAPSHOT_XOFIT:", out_file)

def snapshot_dispatch(args):
    if len(args) >= 1 and args[0].lower() in ["--lite", "lite"]:
        snapshot_lite()
    elif len(args) >= 1 and args[0].lower() in ["--full", "full"]:
        snapshot_full()
    elif len(args) >= 1 and args[0].lower() in ["--xofit", "xofit", "x:o:fit"]:
        snapshot_xofit()
    else:
        snapshot_lite()


def map_depth(depth=1):
    try:
        depth = int(depth)
    except Exception:
        depth = 1

    if depth < 1:
        depth = 1
    if depth > 5:
        depth = 5

    print(f"=== AETHIEA MAP DEPTH {depth} ===")
    print("ROOT:", AETHIEA)
    print()

    base_depth = AETHIEA.rstrip(os.sep).count(os.sep)

    for root, dirs, files in os.walk(AETHIEA):
        current_depth = root.rstrip(os.sep).count(os.sep) - base_depth

        if current_depth > depth:
            dirs[:] = []
            continue

        indent = "  " * current_depth
        name = AETHIEA if current_depth == 0 else os.path.basename(root)
        print(f"{indent}{name}/")

        if current_depth < depth:
            for file in sorted(files):
                print(f"{indent}  {file}")

    print("=== END AETHIEA MAP ===")

def map_dispatch(args):
    if len(args) >= 1:
        map_depth(args[0])
    else:
        map_system()


def report_cleanup():
    print("=== CLEANUP DETECTOR REPORT ===")
    print("MODE: flag_only")
    print("NO_AUTO_DELETE: true")
    print()

    flags = []

    # 1. glued cd artifact folders
    for root, dirs, files in os.walk(AETHIEA):
        for d in dirs:
            if d.endswith("cd"):
                flags.append(("GLUED_CD_DIR", os.path.join(root, d)))

    # 2. empty execution operational dirs
    execution_watch = ["RUNTIME", "OUTPUT", "JOBS", "EXPORTS"]
    for name in execution_watch:
        path = os.path.join(AETHIEA, "EXECUTION", name)
        if os.path.isdir(path) and _count_files(path) == 0:
            flags.append(("EMPTY_EXECUTION_DIR", path))

    # 3. excessive backups in CORE
    core = os.path.join(AETHIEA, "CORE")
    if os.path.isdir(core):
        backups = [x for x in os.listdir(core) if ".bak." in x]
        if len(backups) >= 10:
            flags.append(("HIGH_BACKUP_COUNT", f"{core} backups={len(backups)}"))

    # 4. missing domain mapping/binding
    domains = os.path.join(AETHIEA, "DOMAINS")
    if os.path.isdir(domains):
        for lane in os.listdir(domains):
            lane_path = os.path.join(domains, lane)
            if not os.path.isdir(lane_path):
                continue
            for entity in os.listdir(lane_path):
                epath = os.path.join(lane_path, entity)
                if not os.path.isdir(epath):
                    continue
                mapping = os.path.join(epath, "MAPPING.json")
                binding = os.path.join(epath, "BINDING.json")
                if not os.path.isfile(mapping):
                    flags.append(("MISSING_MAPPING", epath))
                if not os.path.isfile(binding):
                    flags.append(("MISSING_BINDING", epath))

    # 5. stale partial ollama blobs
    ollama_blobs = os.path.join(AETHIEA, "DATA", "OLLAMA", "blobs")
    if os.path.isdir(ollama_blobs):
        for name in os.listdir(ollama_blobs):
            if "partial" in name:
                flags.append(("OLLAMA_PARTIAL_BLOB", os.path.join(ollama_blobs, name)))

    if not flags:
        print("STATUS: clean")
    else:
        print(f"FLAGS: {len(flags)}")
        for kind, path in flags:
            print(f"{kind}: {path}")

    print("=== END CLEANUP DETECTOR REPORT ===")

def main():
    if not AETHIEA:
        print("AETHIEA is not set")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("usage: aeth <status|hosts|logs|validate|session|anchor|scan|write|health|route|memory|bae>")
        sys.exit(1)

    if len(sys.argv) >= 4 and sys.argv[1].lower() == "execute" and sys.argv[2].lower() == "entity":
        execute_entity(" ".join(sys.argv[3:]))
        return

    if universal_dispatch(sys.argv[1:]):
        return

    cmd = sys.argv[1].lower()

    if cmd == "status":
        status()
    elif cmd == "hosts":
        hosts()
    elif cmd == "logs":
        logs()
    elif cmd == "health":
        health()
    elif cmd == "bae":
        if len(sys.argv) < 3:
            print("usage: aeth bae <id>")
        else:
            bae_call(sys.argv[2])
    elif cmd == "validate":
        validate()
    elif cmd == "session":
        session()
    elif cmd == "anchor":
        if len(sys.argv) >= 4 and sys.argv[2].lower() == "find":
            anchor_find(" ".join(sys.argv[3:]))
        else:
            anchor()
    elif cmd == "scan":
        scan()
    elif cmd == "hud":
        if len(sys.argv) < 3 or sys.argv[2].lower() != "ae1of1":
            print("usage: aeth hud ae1of1")
            return
        hud_ae1of1_latest()
    elif cmd == "report":
        if len(sys.argv) >= 3 and sys.argv[2].lower() == "pipelines":
            report_pipelines()
        elif len(sys.argv) >= 3 and sys.argv[2].lower() == "safety":
            report_safety()
        elif len(sys.argv) >= 3 and sys.argv[2].lower() == "security":
            report_safety()
        elif len(sys.argv) >= 3 and sys.argv[2].lower() == "memory":
            report_memory()
        elif len(sys.argv) >= 3 and sys.argv[2].lower() == "domains":
            report_domains()
        elif len(sys.argv) >= 3 and sys.argv[2].lower() == "execution":
            report_execution()
        elif len(sys.argv) >= 3 and sys.argv[2].lower() == "mods":
            report_mods()
        elif len(sys.argv) >= 3 and sys.argv[2].lower() == "rejects":
            report_rejects()
        elif len(sys.argv) >= 3 and sys.argv[2].lower() in ["reject-classes", "reject_classes", "classify"]:
            report_reject_classes()
        elif len(sys.argv) >= 3 and sys.argv[2].lower() in ["reject-reasons", "reject_reasons", "reasons"]:
            report_reject_reasons()
        elif len(sys.argv) >= 3 and sys.argv[2].lower() in ["retry-matrix", "retry_matrix", "retry"]:
            report_retry_matrix()
        elif len(sys.argv) >= 3 and sys.argv[2].lower() == "pending":
            report_pending()
        elif len(sys.argv) >= 3 and sys.argv[2].lower() == "latest":
            report_latest()
        elif len(sys.argv) >= 3 and sys.argv[2].lower() == "health":
            report_health()
        elif len(sys.argv) >= 3 and sys.argv[2].lower() in ["pipeline-health", "pipeline_health", "flags", "reflex"]:
            report_pipeline_health()
        elif len(sys.argv) >= 3 and sys.argv[2].lower() in ["cleanup", "hygiene"]:
            report_cleanup()
        elif len(sys.argv) >= 3 and sys.argv[2].lower() in ["export", "latest-export", "latest_export"]:
            export_latest_report()
        elif len(sys.argv) >= 3 and sys.argv[2].lower() == "all":
            report_all()
        else:
            print("usage: aeth report <all|health|memory|domains|execution|mods|pipelines|rejects|reject-classes|reject-reasons|retry-matrix|pending|latest|pipeline-health|cleanup|export|safety>")
    elif cmd == "map":
        map_dispatch(sys.argv[2:])
    elif cmd == "snapshot":
        snapshot_dispatch(sys.argv[2:])
    elif cmd == "route":
        if len(sys.argv) < 3:
            print("usage: aeth route <command>")
            return
        route_cmd(" ".join(sys.argv[2:]))
    elif cmd == "memory":
        if len(sys.argv) < 4 or sys.argv[2].lower() != "read":
            print("usage: aeth memory read <system|state|session|nodes|routes|layer_map|domain_gcr_execution_map|hosts|anchors>")
            return
        memory_read(sys.argv[3].lower())
    elif cmd == "write":
        if len(sys.argv) >= 3 and sys.argv[2] == "anchor":
            write_anchor(" ".join(sys.argv[3:]))
            return
        if len(sys.argv) < 5:
            print("usage: aeth write <state|session> <key> <value>")
            sys.exit(1)
        target = sys.argv[2].lower()
        key = sys.argv[3]
        value = " ".join(sys.argv[4:])
        write_value(target, key, value)
    else:
        print(f"unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()


# --- AENET ROUTES ---
from pathlib import Path as _AETH_Path
import os as _AETH_os

if "ROOT" not in globals():
    ROOT = _AETH_Path(_AETH_os.environ.get("AETH_ROOT") or _AETH_os.environ.get("AETHIEA") or _AETH_os.popen("aeusb-root 2>/dev/null").read().strip() or str(_AETH_Path.cwd()))
from pathlib import Path as _AETH_Path
import os as _AETH_os

if "ROOT" not in globals():
    ROOT = _AETH_Path(_AETH_os.environ.get("AETH_ROOT") or _AETH_os.environ.get("AETHIEA") or _AETH_os.popen("aeusb-root 2>/dev/null").read().strip() or str(_AETH_Path.cwd()))

AENET = ROOT / "LAYERS" / "AENET"
if "routes" not in globals():
    routes = {}

routes.update({
    "aenet": AENET,
    "cloudflare": AENET / "CLOUDFLARE",
})
