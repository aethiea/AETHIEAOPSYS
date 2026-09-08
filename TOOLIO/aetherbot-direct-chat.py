#!/usr/bin/env python3

import datetime
import json
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import urllib.request

DEFAULT_MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen3:4b"
OPEN_MODEL = "qwen2.5-coder:3b"
OPS_MODEL = "qwen2.5-coder:3b"
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

TOOL_PROTOCOL = f"""AEVPS PROGRAMMING CAPABILITY
You have direct programming tools rooted at {ROOT}.
You may converse normally. Do not force tool use for ordinary conversation.
When the operator asks you to inspect, build, create, edit, patch, fix, validate, or otherwise program AEVPS, use the tools yourself instead of merely printing code or telling the operator to save/run it.
Do not claim a file changed or a check ran unless a tool result confirms it.
Inspect before editing when useful, make the smallest useful change, and validate afterward.

Request exactly one tool at a time using this exact form, with no Markdown fence:
<tool_call>{{"tool":"TOOL_NAME","args":{{...}}}}</tool_call>

Available tools:
- list_dir: {{"path":"relative/path"}}
- read_file: {{"path":"relative/path","start_line":1,"end_line":240}}
- write_file: {{"path":"relative/path","content":"full file text"}}
- replace_text: {{"path":"relative/path","old":"exact old text","new":"replacement text","count":1}}
- make_dir: {{"path":"relative/path"}}
- chmod_exec: {{"path":"relative/path"}}
- run_check: {{"kind":"git_status"}}
- run_check: {{"kind":"git_diff","path":"optional/relative/path"}}
- run_check: {{"kind":"python_compile","path":"relative/file.py"}}
- run_check: {{"kind":"bash_syntax","path":"relative/file.sh"}}
- run_check: {{"kind":"json_parse","path":"relative/file.json"}}

Tool results arrive as a user message beginning with TOOL_RESULT.
After programming work is complete, summarize exactly what changed and which checks passed.
"""

OPS_PROMPT = """You are ÆTHERBOT in forced native AEVPS programming mode.
Prioritize completing the operator's programming task with the available AEVPS tools.
""" + TOOL_PROTOCOL

OPEN_PROMPT = """You are ÆTHERBOT, the operator's local AETHIEA assistant.
Chat naturally for ordinary conversation. You also have native AEVPS programming capability in this same conversation.
""" + TOOL_PROTOCOL

TOOL_RE = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)


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


def execute_tool(call):
    name = call.get("tool")
    args = call.get("args", {})
    if name not in TOOLS:
        return {"ok": False, "tool": name, "error": f"unknown tool: {name}"}
    if not isinstance(args, dict):
        return {"ok": False, "tool": name, "error": "args must be an object"}
    try:
        return {"ok": True, "tool": name, "result": TOOLS[name](args)}
    except Exception as exc:
        audit("tool_error", tool=name, error=str(exc))
        return {"ok": False, "tool": name, "error": str(exc)}


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
        print("system_prompt=CAPABILITY_ONLY")
        print("thinking_mode=NONE")
        print("thinking_display=OFF")
        print(f"programming_root={ROOT}")
        print("tools=list_dir,read_file,write_file,replace_text,make_dir,chmod_exec,run_check")
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
        print("ops_backend=native-aevps-programmer")
        print(f"programming_root={ROOT}")
        print("tools=list_dir,read_file,write_file,replace_text,make_dir,chmod_exec,run_check")
        print(f"audit_log={AUDIT}")


def ollama_chat(model, wire_messages, stream=True, think=None):
    payload = {
        "model": model,
        "messages": wire_messages,
        "stream": stream,
        "options": {"num_ctx": 4096},
    }
    if think is not None:
        payload["think"] = think
    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return urllib.request.urlopen(req, timeout=300)


def run_agent(prompt, forced=False):
    system_prompt = OPS_PROMPT if forced else OPEN_PROMPT
    session = [
        {"role": "system", "content": system_prompt},
        *messages,
        {"role": "user", "content": prompt},
    ]
    messages.append({"role": "user", "content": prompt})
    audit("agent_request", mode="ops" if forced else "open", prompt=prompt)
    print()

    for step in range(1, 13):
        try:
            with ollama_chat(OPEN_MODEL, session, stream=False) as response:
                data = json.loads(response.read())
        except KeyboardInterrupt:
            print("[interrupted]\n")
            messages.pop()
            return
        except Exception as exc:
            print(f"ERROR: {exc}\n")
            messages.pop()
            return

        content = data.get("message", {}).get("content", "").strip()
        if not content:
            print("[no response returned]\n")
            messages.pop()
            return

        match = TOOL_RE.search(content)
        if not match:
            print(content + "\n")
            messages.append({"role": "assistant", "content": content})
            audit("agent_complete", mode="ops" if forced else "open", steps=step, final=content[:4000])
            return

        before = content[:match.start()].strip()
        if before:
            print(before)

        call = {}
        try:
            call = json.loads(match.group(1))
            tool_result = execute_tool(call)
        except json.JSONDecodeError as exc:
            tool_result = {"ok": False, "tool": "unknown", "error": f"invalid tool JSON: {exc}"}

        tool_name = tool_result.get("tool", call.get("tool", "unknown"))
        if tool_result.get("ok"):
            print(f"[tool:{tool_name}] PASS")
        else:
            print(f"[tool:{tool_name}] FAIL: {tool_result.get('error')}")

        session.append({"role": "assistant", "content": content})
        session.append({
            "role": "user",
            "content": "TOOL_RESULT " + json.dumps(tool_result, ensure_ascii=False),
        })

    print("[agent stopped: tool-step limit reached]\n")
    audit("agent_step_limit", mode="ops" if forced else "open", steps=12)


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
