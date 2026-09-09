#!/usr/bin/env python3

import datetime
import json
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import urllib.error
import urllib.request

DEFAULT_MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen3:4b"
OPEN_MODEL = "qwen2.5-coder:3b"
URL = "http://127.0.0.1:11434/api/chat"
ROOT = Path("/opt/AETHIEAOPSYS").resolve()
STATE = ROOT / "STATE" / "aetherbot"
BACKUPS = STATE / "backups"
AUDIT = STATE / "ops-audit.jsonl"

MODE = "open"
messages = []

GROUND_PROMPT = """You are ÆTHERBOT in grounded-context mode.
Use grounded context only when it has actually been supplied to this client.
Do not pretend retrieval occurred when no retrieval result is present.
Keep verified context separate from inference.
/no_think
"""

CHAT_PROMPT = """You are ÆTHERBOT, the operator's local AETHIEA assistant.
Chat naturally and directly. The wrapper can separately route programming requests
into a real AEVPS tool executor rooted at /opt/AETHIEAOPSYS.
"""

PLANNER_PROMPT = f"""You are ÆTHERBOT's AEVPS programming planner.
Your programming root is {ROOT}.

For programming requests, choose exactly one next action. The wrapper executes the
action; you never execute it yourself and you never invent tool results.

Use action=reply only when the requested work is actually complete based on tool
results already present in the conversation. Never claim a file changed or a check
passed unless the wrapper supplied that result.

Available actions and args:
- list_dir: path
- read_file: path, start_line, end_line
- write_file: path, content
- replace_text: path, old, new, count
- make_dir: path
- chmod_exec: path
- run_check: kind, path
  kinds: git_status, git_diff, python_compile, bash_syntax, json_parse
- reply: no tool action; put the final conversational response in message

For create/edit/build requests, perform a mutating action before reply.
For validate/verify/check/test/compile/parse requests, perform run_check before reply.
Inspect existing files before changing them when that is useful.
Keep each step small and use one action at a time.
"""

PROGRAMMING_RE = re.compile(
    r"\b(inspect|build|create|edit|patch|fix|validate|verify|check|test|compile|lint|"
    r"write|change|update|modify|make|chmod|program|implement|refactor|delete|remove|"
    r"rename|move|copy|save|install)\b",
    re.IGNORECASE,
)
MUTATION_RE = re.compile(
    r"\b(build|create|edit|patch|fix|write|change|update|modify|make|chmod|program|"
    r"implement|refactor|delete|remove|rename|move|copy|save|install)\b",
    re.IGNORECASE,
)
VALIDATION_RE = re.compile(
    r"\b(validate|verify|check|test|compile|lint|parse)\b",
    re.IGNORECASE,
)
MUTATING_TOOLS = {"write_file", "replace_text", "make_dir", "chmod_exec"}

ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [
                "reply",
                "list_dir",
                "read_file",
                "write_file",
                "replace_text",
                "make_dir",
                "chmod_exec",
                "run_check",
            ],
        },
        "args": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "start_line": {"type": "integer"},
                "end_line": {"type": "integer"},
                "content": {"type": "string"},
                "old": {"type": "string"},
                "new": {"type": "string"},
                "count": {"type": "integer"},
                "kind": {
                    "type": "string",
                    "enum": [
                        "git_status",
                        "git_diff",
                        "python_compile",
                        "bash_syntax",
                        "json_parse",
                    ],
                },
            },
        },
        "message": {"type": "string"},
    },
    "required": ["action", "args", "message"],
}


def now_stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ensure_state():
    BACKUPS.mkdir(parents=True, exist_ok=True)


def audit(event, **fields):
    ensure_state()
    record = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "event": event,
        **fields,
    }
    with AUDIT.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def safe_path(value):
    value = value or "."
    candidate = Path(value)
    resolved = candidate.resolve() if candidate.is_absolute() else (ROOT / candidate).resolve()
    if resolved != ROOT and ROOT not in resolved.parents:
        raise ValueError(f"path escapes AEVPS root: {value}")
    return resolved


def relative_name(path):
    return str(path.relative_to(ROOT)) if path != ROOT else "."


def backup_existing(path):
    if not path.exists() or not path.is_file():
        return None
    destination = BACKUPS / now_stamp() / path.relative_to(ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
    return relative_name(destination)


def tool_list_dir(args):
    path = safe_path(args.get("path", "."))
    if not path.is_dir():
        raise ValueError("not a directory")
    entries = []
    for child in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        entries.append({
            "name": child.name,
            "kind": "dir" if child.is_dir() else "file",
            "size": child.stat().st_size if child.is_file() else None,
        })
        if len(entries) >= 200:
            break
    return {"path": relative_name(path), "entries": entries}


def tool_read_file(args):
    path = safe_path(args["path"])
    if not path.is_file():
        raise ValueError("not a file")
    start = max(1, int(args.get("start_line", 1)))
    end = max(start, int(args.get("end_line", start + 239)))
    end = min(end, start + 499)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    selected = lines[start - 1:end]
    return {
        "path": relative_name(path),
        "start_line": start,
        "end_line": start + len(selected) - 1,
        "total_lines": len(lines),
        "content": "\n".join(selected),
    }


def tool_write_file(args):
    path = safe_path(args["path"])
    content = args["content"]
    if not isinstance(content, str):
        raise ValueError("content must be text")
    backup = backup_existing(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    audit("write_file", path=relative_name(path), backup=backup, bytes=len(content.encode("utf-8")))
    return {"path": relative_name(path), "bytes": len(content.encode("utf-8")), "backup": backup}


def tool_replace_text(args):
    path = safe_path(args["path"])
    old = args["old"]
    new = args["new"]
    count = int(args.get("count", 1))
    if not path.is_file():
        raise ValueError("not a file")
    if not isinstance(old, str) or not isinstance(new, str) or not old:
        raise ValueError("old/new must be text and old must be non-empty")
    text = path.read_text(encoding="utf-8", errors="strict")
    occurrences = text.count(old)
    if occurrences == 0:
        raise ValueError("old text not found")
    if count < 0:
        raise ValueError("count must be >= 0")
    backup = backup_existing(path)
    replaced = text.replace(old, new, count if count else occurrences)
    path.write_text(replaced, encoding="utf-8")
    applied = min(occurrences, count) if count else occurrences
    audit("replace_text", path=relative_name(path), backup=backup, replacements=applied)
    return {"path": relative_name(path), "replacements": applied, "backup": backup}


def tool_make_dir(args):
    path = safe_path(args["path"])
    path.mkdir(parents=True, exist_ok=True)
    audit("make_dir", path=relative_name(path))
    return {"path": relative_name(path), "created": True}


def tool_chmod_exec(args):
    path = safe_path(args["path"])
    if not path.is_file():
        raise ValueError("not a file")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    audit("chmod_exec", path=relative_name(path))
    return {"path": relative_name(path), "executable": True}


def run_argv(argv, cwd=ROOT, timeout=60):
    completed = subprocess.run(
        argv,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    return {"exit_code": completed.returncode, "output": completed.stdout[-20000:]}


def tool_run_check(args):
    kind = args["kind"]
    path_arg = args.get("path")

    if kind == "git_status":
        result = run_argv(["git", "-C", str(ROOT), "status", "--short"])
    elif kind == "git_diff":
        argv = ["git", "-C", str(ROOT), "diff", "--"]
        if path_arg:
            argv.append(relative_name(safe_path(path_arg)))
        result = run_argv(argv)
    elif kind == "python_compile":
        result = run_argv(["python3", "-m", "py_compile", str(safe_path(path_arg))])
    elif kind == "bash_syntax":
        result = run_argv(["bash", "-n", str(safe_path(path_arg))])
    elif kind == "json_parse":
        path = safe_path(path_arg)
        try:
            json.loads(path.read_text(encoding="utf-8"))
            result = {"exit_code": 0, "output": "JSON parse PASS"}
        except Exception as exc:
            result = {"exit_code": 1, "output": f"JSON parse FAIL: {exc}"}
    else:
        raise ValueError(f"unsupported check kind: {kind}")

    audit("run_check", kind=kind, path=path_arg, exit_code=result["exit_code"])
    return {"kind": kind, "path": path_arg, **result}


TOOLS = {
    "list_dir": tool_list_dir,
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "replace_text": tool_replace_text,
    "make_dir": tool_make_dir,
    "chmod_exec": tool_chmod_exec,
    "run_check": tool_run_check,
}


def execute_tool(action, args):
    if action not in TOOLS:
        return {"ok": False, "tool": action, "error": f"unknown tool: {action}"}
    if not isinstance(args, dict):
        return {"ok": False, "tool": action, "error": "args must be an object"}
    try:
        result = TOOLS[action](args)
        return {"ok": True, "tool": action, "result": result}
    except Exception as exc:
        audit("tool_error", tool=action, error=str(exc))
        return {"ok": False, "tool": action, "error": str(exc)}


def active_model():
    if MODE in {"open", "ops"}:
        return OPEN_MODEL
    return DEFAULT_MODEL


def clear_for_mode(new_mode):
    global MODE
    MODE = new_mode
    messages.clear()
    print(f"mode={MODE}")
    print(f"model={active_model()}")
    print("conversation cleared")


def status():
    print(f"model={active_model()}")
    print("provider=ollama")
    print("codex=OFF")
    print("endpoint=/api/chat")
    print(f"mode={MODE}")

    if MODE == "open":
        print("chat=ON")
        print("autonomous_programming=ON")
        print("open_model=qwen2.5-coder:3b")
        print("planner=OLLAMA_STRUCTURED_JSON")
        print("thinking_mode=NONE")
        print("thinking_display=OFF")
        print(f"programming_root={ROOT}")
        print("tools=list_dir,read_file,write_file,replace_text,make_dir,chmod_exec,run_check")
        print("tool_result_auth=WRAPPER_ONLY")
        print("programming_completion=REQUIRES_REAL_TOOL_PASS")
        print(f"audit_log={AUDIT}")
        print("aemcp=false")
        print("topology=false")
        print("vrag=false")
        print("b43=false")
    elif MODE == "ground":
        print("chat=ON")
        print("streaming=ON")
        print("thinking_mode=qwen3-no_think")
        print("thinking_display=OFF")
        print("ground_backend=not-connected-in-direct-client")
    elif MODE == "ops":
        print("chat=ON")
        print("autonomous_programming=FORCED")
        print("ops_model=qwen2.5-coder:3b")
        print("planner=OLLAMA_STRUCTURED_JSON")
        print("ops_backend=native-aevps-programmer")
        print(f"programming_root={ROOT}")
        print("tools=list_dir,read_file,write_file,replace_text,make_dir,chmod_exec,run_check")
        print("tool_result_auth=WRAPPER_ONLY")
        print("programming_completion=REQUIRES_REAL_TOOL_PASS")
        print(f"audit_log={AUDIT}")


def ollama_chat(model, wire_messages, stream=True, think=None, format_value=None, temperature=None):
    payload = {
        "model": model,
        "messages": wire_messages,
        "stream": stream,
        "options": {"num_ctx": 4096},
    }
    if temperature is not None:
        payload["options"]["temperature"] = temperature
    if think is not None:
        payload["think"] = think
    if format_value is not None:
        payload["format"] = format_value

    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return urllib.request.urlopen(req, timeout=300)


def request_requirements(prompt, forced=False):
    programming_required = forced or bool(PROGRAMMING_RE.search(prompt))
    mutation_required = bool(MUTATION_RE.search(prompt))
    validation_required = bool(VALIDATION_RE.search(prompt))
    return programming_required, mutation_required, validation_required


def unmet_requirements(programming_required, mutation_required, validation_required,
                       tool_passes, mutation_passes, validation_passes):
    unmet = []
    if programming_required and tool_passes == 0:
        unmet.append("no real tool has executed successfully")
    if mutation_required and mutation_passes == 0:
        unmet.append("no mutating tool has executed successfully")
    if validation_required and validation_passes == 0:
        unmet.append("no validation run_check has passed")
    return unmet


def summarize_tool_pass(tool_name, tool_result):
    result = tool_result.get("result", {})
    details = []
    if isinstance(result, dict):
        for key in ("path", "kind", "bytes", "replacements", "exit_code"):
            if key in result and result[key] is not None:
                details.append(f"{key}={result[key]}")
    suffix = " " + " ".join(details) if details else ""
    print(f"[tool:{tool_name}] PASS{suffix}")


def run_chat(prompt):
    wire = [
        {"role": "system", "content": CHAT_PROMPT},
        *messages,
        {"role": "user", "content": prompt},
    ]
    messages.append({"role": "user", "content": prompt})
    answer = []

    try:
        with ollama_chat(OPEN_MODEL, wire, stream=True) as response:
            print()
            for raw in response:
                raw = raw.strip()
                if not raw:
                    continue
                content = json.loads(raw).get("message", {}).get("content", "")
                if content:
                    print(content, end="", flush=True)
                    answer.append(content)
            print("\n")
    except KeyboardInterrupt:
        print("\n[interrupted]\n")
        messages.pop()
        return
    except Exception as exc:
        print(f"\nERROR: {exc}\n")
        messages.pop()
        return

    final = "".join(answer).strip()
    if final:
        messages.append({"role": "assistant", "content": final})


def planner_step(session):
    try:
        with ollama_chat(
            OPEN_MODEL,
            session,
            stream=False,
            format_value=ACTION_SCHEMA,
            temperature=0,
        ) as response:
            data = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        if exc.code != 400:
            raise
        # Fallback for an older Ollama build: still force JSON mode.
        with ollama_chat(
            OPEN_MODEL,
            session,
            stream=False,
            format_value="json",
            temperature=0,
        ) as response:
            data = json.loads(response.read())

    content = data.get("message", {}).get("content", "").strip()
    if not content:
        raise ValueError("planner returned empty content")
    decision = json.loads(content)
    if not isinstance(decision, dict):
        raise ValueError("planner response is not an object")
    action = decision.get("action")
    args = decision.get("args", {})
    message = decision.get("message", "")
    if action not in set(ACTION_SCHEMA["properties"]["action"]["enum"]):
        raise ValueError(f"planner returned unsupported action: {action}")
    if not isinstance(args, dict):
        raise ValueError("planner args are not an object")
    if not isinstance(message, str):
        raise ValueError("planner message is not text")
    return {"action": action, "args": args, "message": message}


def run_agent(prompt, forced=False):
    programming_required, mutation_required, validation_required = request_requirements(
        prompt, forced=forced
    )

    if not programming_required and not forced:
        run_chat(prompt)
        return

    mode_name = "ops" if forced else "open"
    session = [
        {"role": "system", "content": PLANNER_PROMPT},
        *messages,
        {"role": "user", "content": prompt},
    ]
    messages.append({"role": "user", "content": prompt})
    audit(
        "agent_request",
        mode=mode_name,
        prompt=prompt,
        programming_required=programming_required,
        mutation_required=mutation_required,
        validation_required=validation_required,
        planner="structured_json",
    )
    print()

    tool_passes = 0
    mutation_passes = 0
    validation_passes = 0

    for step in range(1, 13):
        try:
            decision = planner_step(session)
        except KeyboardInterrupt:
            print("[interrupted]\n")
            messages.pop()
            return
        except Exception as exc:
            print(f"[planner] FAIL: {exc}")
            audit("planner_error", mode=mode_name, step=step, error=str(exc))
            session.append({
                "role": "user",
                "content": (
                    "PLANNER_ERROR: return one valid JSON object matching the required schema. "
                    f"Previous error: {exc}"
                ),
            })
            continue

        action = decision["action"]
        args = decision["args"]
        message = decision["message"].strip()

        if action == "reply":
            unmet = unmet_requirements(
                programming_required,
                mutation_required,
                validation_required,
                tool_passes,
                mutation_passes,
                validation_passes,
            )
            if unmet:
                reason_text = "; ".join(unmet)
                print(f"[planner] CONTINUE: {reason_text}")
                audit("planner_continue", mode=mode_name, step=step, reason=reason_text)
                session.append({
                    "role": "assistant",
                    "content": json.dumps(decision, ensure_ascii=False),
                })
                session.append({
                    "role": "user",
                    "content": (
                        "WRAPPER_REQUIREMENT: completion rejected because " + reason_text + ". "
                        "Choose the required real tool action next."
                    ),
                })
                continue

            final = message or "Completed."
            print(final + "\n")
            messages.append({"role": "assistant", "content": final})
            audit(
                "agent_complete",
                mode=mode_name,
                steps=step,
                tool_passes=tool_passes,
                mutation_passes=mutation_passes,
                validation_passes=validation_passes,
                final=final[:4000],
            )
            return

        tool_result = execute_tool(action, args)
        if tool_result.get("ok"):
            tool_passes += 1
            if action in MUTATING_TOOLS:
                mutation_passes += 1
            if (
                action == "run_check"
                and tool_result.get("result", {}).get("exit_code") == 0
            ):
                validation_passes += 1
            summarize_tool_pass(action, tool_result)
        else:
            print(f"[tool:{action}] FAIL: {tool_result.get('error')}")

        session.append({
            "role": "assistant",
            "content": json.dumps(decision, ensure_ascii=False),
        })
        session.append({
            "role": "user",
            "content": "WRAPPER_TOOL_RESULT " + json.dumps(tool_result, ensure_ascii=False),
        })

    print("[agent stopped: tool-step limit reached]\n")
    audit(
        "agent_step_limit",
        mode=mode_name,
        steps=12,
        tool_passes=tool_passes,
        mutation_passes=mutation_passes,
        validation_passes=validation_passes,
    )


def run_ground(prompt):
    messages.append({"role": "user", "content": prompt})
    wire = [
        {"role": "system", "content": GROUND_PROMPT},
        *messages[:-1],
        {"role": "user", "content": f"{prompt}\n\n/no_think"},
    ]
    answer = []
    initial_buffer = ""
    answer_mode = False

    try:
        with ollama_chat(DEFAULT_MODEL, wire, stream=True, think=False) as response:
            print()
            for raw in response:
                raw = raw.strip()
                if not raw:
                    continue
                content = json.loads(raw).get("message", {}).get("content", "")
                if not content:
                    continue
                if not answer_mode:
                    initial_buffer += content
                    marker = initial_buffer.find("</think>")
                    if marker != -1:
                        answer_mode = True
                        visible = initial_buffer[marker + len("</think>"):].lstrip()
                        initial_buffer = ""
                        if visible:
                            print(visible, end="", flush=True)
                            answer.append(visible)
                    continue
                print(content, end="", flush=True)
                answer.append(content)

            if not answer_mode and initial_buffer.strip():
                clean = initial_buffer.strip()
                print(clean, end="", flush=True)
                answer.append(clean)
            print("\n")
    except KeyboardInterrupt:
        print("\n[interrupted]\n")
        messages.pop()
        return
    except Exception as exc:
        print(f"\nERROR: {exc}\n")
        messages.pop()
        return

    final = "".join(answer).strip()
    if final:
        messages.append({"role": "assistant", "content": final})


ensure_state()
print(f"ÆTHERBOT // CHAT+PROGRAM {OPEN_MODEL} // DIRECT OLLAMA")
print("Mode: open")
print("Commands: /open  /ground  /ops  /mode  /status  /clear  /bye")

while True:
    try:
        prompt = input(">>> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        break

    if not prompt:
        continue
    if prompt in {"/bye", "/exit", "/quit"}:
        break
    if prompt == "/clear":
        messages.clear()
        print("conversation cleared")
        continue
    if prompt == "/open":
        clear_for_mode("open")
        continue
    if prompt == "/ground":
        clear_for_mode("ground")
        continue
    if prompt == "/ops":
        clear_for_mode("ops")
        continue
    if prompt == "/mode":
        print(f"mode={MODE}")
        print(f"model={active_model()}")
        continue
    if prompt == "/status":
        status()
        continue

    if MODE == "ground":
        run_ground(prompt)
    elif MODE == "ops":
        run_agent(prompt, forced=True)
    else:
        run_agent(prompt, forced=False)
