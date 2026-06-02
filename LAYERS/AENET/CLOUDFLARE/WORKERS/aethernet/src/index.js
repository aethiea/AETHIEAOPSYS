const WORKERS_AI_MODELS = {
  llama: "@cf/meta/llama-3.2-3b-instruct",
  mistral: "@cf/mistral/mistral-7b-instruct-v0.1"
};

async function askHuggingFace(prompt, model, token) {
  if (!token) {
    return { error: "HF_TOKEN_MISSING" };
  }

  const res = await fetch(`https://router.huggingface.co/hf-inference/models/${model}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      inputs: prompt,
      parameters: {
        max_new_tokens: 64,
        return_full_text: false
      }
    })
  });

  const text = await res.text();

  try {
    return {
      ok: res.ok,
      status: res.status,
      data: JSON.parse(text)
    };
  } catch {
    return {
      ok: res.ok,
      status: res.status,
      raw: text
    };
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/status") {
      return Response.json({
        hub: env.AENET_NAME || "AENET_EDGE",
        worker: "aethernet",
        status: "ONLINE",
        workers_ai: !!env.AI,
        hf_token: !!env.HF_TOKEN,
        routes: ["/status", "/capabilities", "/models", "/policy", "/ask"]
      });
    }

    if (url.pathname === "/capabilities") {
      return Response.json({
        capabilities: ["cloudflare", "workers-ai", "huggingface", "chatgpt", "github"]
      });
    }


    if (url.pathname === "/policy") {
      return Response.json({
        hub: env.AENET_NAME || "AENET_EDGE",
        policy: "AENET_PROVIDER_POLICY",
        default_provider: "workers-ai",
        default_model: "llama",
        providers: {
          "workers-ai": {
            status: "verified_active",
            role: "default heartbeat",
            automatic: true
          },
          "huggingface": {
            status: env.HF_TOKEN ? "token_ready" : "token_missing",
            role: "fallback / model-library lane",
            automatic: false
          },
          "openai": {
            status: "quota_gated",
            role: "premium provider lane",
            automatic: false
          }
        },
        rules: [
          "Workers AI is default heartbeat.",
          "OpenAI is explicit-only while quota-gated.",
          "Premium compute is not default.",
          "No provider becomes the body."
        ]
      });
    }

    if (url.pathname === "/models") {
      return Response.json({
        workers_ai: WORKERS_AI_MODELS,
        huggingface: {
          mistral: "mistralai/Mistral-7B-Instruct-v0.3"
        }
      });
    }

    if (url.pathname === "/ask") {
      const body = await request.json().catch(() => ({}));
      const prompt = body.prompt || "Say AENET Door active.";
      const provider = body.provider || "workers-ai";
      const modelKey = body.model || "llama";

      if (provider === "huggingface") {
        const model = modelKey === "test"
          ? "gpt2"
          : modelKey;

        const result = await askHuggingFace(prompt, model, env.HF_TOKEN);

        return Response.json({
          hub: "AENET_EDGE",
          provider: "huggingface",
          model,
          prompt,
          result
        });
      }

      const model = WORKERS_AI_MODELS[modelKey] || modelKey;

      const system = `You are AETHERNet, the AENET edge worker for AETHIEAOPSYS.
AENET means AETHIEA network/routing membrane, not any public acronym.
AEUSB is the current runtime surface.
Answer as a concise system-status agent.
Do not reinterpret AENET as television, flight simulator, or unrelated public entities.`;

      const result = await env.AI.run(model, {
        messages: [
          { role: "system", content: system },
          { role: "user", content: prompt }
        ]
      });

      return Response.json({
        hub: "AENET_EDGE",
        provider: "cloudflare-workers-ai",
        model,
        prompt,
        result
      });
    }

    return Response.json({ hub: "AENET_EDGE", status: "READY" });
  }
}
