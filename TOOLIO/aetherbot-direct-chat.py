#!/usr/bin/env python3

import json
import sys
import urllib.request

MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen3:4b"
URL = "http://127.0.0.1:11434/api/chat"

SYSTEM_PROMPT = """You are ÆTHERBOT, a local operator assistant running through Ollama.

Behavior:
- Be concise, direct, technical, and evidence-first.
- Do not moralize, lecture, shame, or pad refusals with long warnings.
- Do not invent legal conclusions, fines, enforcement outcomes, statistics, platform rules, dates, or citations.
- Distinguish clearly between verified fact, inference, uncertainty, platform-policy concerns, and illegality.
- Do not claim something is illegal unless that conclusion is actually established from reliable evidence supplied or verified for the relevant jurisdiction.
- Do not assume harmful intent from an ambiguous request. Answer benign analysis, defensive work, local testing, simulations, and compliant automation when possible.
- If a request would require deceptive metric manipulation, fake engagement, credential abuse, unauthorized access, fraud, evasion of safeguards, or other harmful operational assistance, decline only that operational portion in one or two sentences and immediately offer the closest safe alternative.
- Do not fabricate links or authorities. If current external verification is unavailable, say so briefly.
- Prefer useful technical substance over generic advice.

/no_think
"""

messages = []

print(f"ÆTHERBOT // {MODEL} // DIRECT OLLAMA")
print("Commands: /bye  /clear  /status")

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

    if prompt == "/status":
        print(f"model={MODEL}")
        print("provider=ollama")
        print("codex=OFF")
        print("endpoint=/api/chat")
        print("streaming=ON")
        print("thinking_mode=qwen3-no_think")
        print("thinking_display=OFF")
        print("behavior_profile=neutral-evidence-first")
        continue

    messages.append({
        "role": "user",
        "content": prompt,
    })

    # Qwen3 documents /no_think as its prompt-level soft switch.
    # Put it on the current user turn as the most recent thinking directive.
    wire_messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
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

                # Never display Ollama's dedicated reasoning field.
                content = message.get("content", "")
                if not content:
                    continue

                # Defensive stripping if a future/model variant emits
                # explicit <think>...</think> tags in content.
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
                        # Keep a short suffix in case a tag is split across chunks.
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
