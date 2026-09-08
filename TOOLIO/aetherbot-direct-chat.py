#!/usr/bin/env python3

import json
import sys
import urllib.request

DEFAULT_MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen3:4b"
OPEN_MODEL = "qwen2.5-coder:3b"
URL = "http://127.0.0.1:11434/api/chat"

MODE = "open"
messages = []

MODE_PROMPTS = {
    "ground": """You are ÆTHERBOT in grounded-context mode.
Use grounded context only when it has actually been supplied to this client.
Do not pretend retrieval occurred when no retrieval result is present.
Keep verified context separate from inference.
/no_think
""",
    "ops": """You are ÆTHERBOT in governed operations mode.
Be precise about what has and has not actually executed.
Do not claim a tool, shell command, MCP action, VRAG lookup, or topology action ran unless a real result is present.
/no_think
""",
}


def active_model():
    return OPEN_MODEL if MODE == "open" else DEFAULT_MODEL


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
    print("streaming=ON")
    print(f"mode={MODE}")

    if MODE == "open":
        print("open_model=qwen2.5-coder:3b")
        print("system_prompt=NONE")
        print("thinking_mode=NONE")
        print("thinking_display=OFF")
        print("llama=true")
        print("aemcp=false")
        print("topology=false")
        print("vrag=false")
        print("b43=false")
    elif MODE == "ground":
        print("thinking_mode=qwen3-no_think")
        print("thinking_display=OFF")
        print("ground_backend=not-connected-in-direct-client")
    elif MODE == "ops":
        print("thinking_mode=qwen3-no_think")
        print("thinking_display=OFF")
        print("ops_backend=not-connected-in-direct-client")


print(f"ÆTHERBOT // OPEN {OPEN_MODEL} // DIRECT OLLAMA")
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

    messages.append({
        "role": "user",
        "content": prompt,
    })

    model = active_model()

    if MODE == "open":
        # Earlier free-form local lane: no wrapper policy/system prompt.
        wire_messages = list(messages)
    else:
        wire_messages = [
            {
                "role": "system",
                "content": MODE_PROMPTS[MODE],
            },
            *messages[:-1],
            {
                "role": "user",
                "content": f"{prompt}\n\n/no_think",
            },
        ]

    payload = {
        "model": model,
        "messages": wire_messages,
        "stream": True,
        "options": {
            "num_ctx": 4096
        }
    }

    # Ollama/Qwen3 thinking control is only relevant outside open mode.
    if MODE != "open" and model.startswith("qwen3"):
        payload["think"] = False

    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    answer = []

    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            print()

            # qwen2.5-coder open lane streams content directly.
            if MODE == "open":
                for raw in response:
                    raw = raw.strip()
                    if not raw:
                        continue

                    data = json.loads(raw)
                    content = data.get("message", {}).get("content", "")
                    if content:
                        print(content, end="", flush=True)
                        answer.append(content)

            else:
                # Qwen3 defensive reasoning suppression for ground/ops.
                initial_buffer = ""
                answer_mode = False

                for raw in response:
                    raw = raw.strip()
                    if not raw:
                        continue

                    data = json.loads(raw)
                    content = data.get("message", {}).get("content", "")
                    if not content:
                        continue

                    if not answer_mode:
                        initial_buffer += content
                        marker = initial_buffer.find("</think>")

                        if marker != -1:
                            answer_mode = True
                            visible = initial_buffer[
                                marker + len("</think>"):
                            ].lstrip()
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
        continue
    except Exception as exc:
        print(f"\nERROR: {exc}\n")
        messages.pop()
        continue

    final = "".join(answer).strip()

    if final:
        messages.append({
            "role": "assistant",
            "content": final,
        })
    else:
        print("[no final answer returned]")
