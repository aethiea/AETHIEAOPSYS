#!/usr/bin/env python3

import json
import sys
import urllib.request

MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen3:4b"
URL = "http://127.0.0.1:11434/api/chat"

MODE = "open"
messages = []

MODE_PROMPTS = {
    "open": """You are ÆTHERBOT, the local AETHIEA conversational assistant.
Converse naturally with the operator.
Do not force retrieval, evidence templates, operations framing, topology, VRAG, AEMCP, or B43 into ordinary conversation.
Keep the response direct and useful.
/no_think
""",
    "ground": """You are ÆTHERBOT in grounded-context mode.
Use grounded context when it has actually been supplied to this client.
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


def clear_for_mode(new_mode):
    global MODE
    MODE = new_mode
    messages.clear()
    print(f"mode={MODE}")
    print("conversation cleared")


def status():
    print(f"model={MODEL}")
    print("provider=ollama")
    print("codex=OFF")
    print("endpoint=/api/chat")
    print("streaming=ON")
    print("thinking_mode=qwen3-no_think")
    print("thinking_display=OFF")
    print(f"mode={MODE}")

    if MODE == "open":
        print("llama=true")
        print("aemcp=false")
        print("topology=false")
        print("vrag=false")
        print("b43=false")
    elif MODE == "ground":
        print("ground_backend=not-connected-in-direct-client")
    elif MODE == "ops":
        print("ops_backend=not-connected-in-direct-client")


print(f"ÆTHERBOT // {MODEL} // DIRECT OLLAMA")
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
        continue

    if prompt == "/status":
        status()
        continue

    messages.append({
        "role": "user",
        "content": prompt,
    })

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
        "model": MODEL,
        "messages": wire_messages,
        "stream": True,
        "think": False,
        "options": {
            "num_ctx": 4096
        }
    }

    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    answer = []
    suppress_tagged_think = False
    tag_buffer = ""

    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            print()

            for raw in response:
                raw = raw.strip()
                if not raw:
                    continue

                data = json.loads(raw)
                message = data.get("message", {})
                content = message.get("content", "")

                if not content:
                    continue

                tag_buffer += content

                while tag_buffer:
                    if suppress_tagged_think:
                        end = tag_buffer.find("</think>")
                        if end == -1:
                            tag_buffer = ""
                            break
                        tag_buffer = tag_buffer[end + len("</think>"):]
                        suppress_tagged_think = False
                        continue

                    start = tag_buffer.find("<think>")
                    if start == -1:
                        keep = min(len(tag_buffer), len("<think>") - 1)
                        emit = tag_buffer[:-keep] if keep else tag_buffer
                        tag_buffer = tag_buffer[-keep:] if keep else ""
                        if emit:
                            print(emit, end="", flush=True)
                            answer.append(emit)
                        break

                    visible = tag_buffer[:start]
                    if visible:
                        print(visible, end="", flush=True)
                        answer.append(visible)
                    tag_buffer = tag_buffer[start + len("<think>"):]
                    suppress_tagged_think = True

            if tag_buffer and not suppress_tagged_think:
                print(tag_buffer, end="", flush=True)
                answer.append(tag_buffer)

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
