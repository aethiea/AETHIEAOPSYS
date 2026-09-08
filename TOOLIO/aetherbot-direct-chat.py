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
- Distinguish clearly between: verified fact, inference, uncertainty, platform-policy concerns, and illegality.
- Do not claim something is illegal unless that conclusion is actually established from reliable evidence supplied or verified for the relevant jurisdiction.
- Do not assume harmful intent from an ambiguous request. Answer benign analysis, defensive work, local testing, simulations, and compliant automation when possible.
- If a request would require deceptive metric manipulation, fake engagement, credential abuse, unauthorized access, fraud, evasion of safeguards, or other harmful operational assistance, decline only that operational portion in one or two sentences and immediately offer the closest safe alternative.
- Do not fabricate links or authorities. If current external verification is unavailable, say so briefly.
- Prefer useful technical substance over generic advice.
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
        print("thinking_display=OFF")
        print("behavior_profile=neutral-evidence-first")
        continue

    messages.append({
        "role": "user",
        "content": prompt,
    })

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            *messages,
        ],
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
    initial_buffer = ""
    answer_mode = False

    try:
        with urllib.request.urlopen(req, timeout=300) as response:

            for raw in response:
                raw = raw.strip()
                if not raw:
                    continue

                data = json.loads(raw)
                message = data.get("message", {})
                content = message.get("content", "")

                if not content:
                    continue

                if not answer_mode:
                    initial_buffer += content

                    # Current Qwen3/Ollama path can leak reasoning first
                    # and terminate it with </think>.
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

            # Fallback: if Ollama fixes think:false and sends no
            # reasoning marker, treat the buffered text as the answer.
            if not answer_mode and initial_buffer.strip():
                clean = initial_buffer.strip()
                print(clean, end="", flush=True)
                answer.append(clean)

            print("\n")

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
