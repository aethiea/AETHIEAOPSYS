const url =
  "https://gateway.ai.cloudflare.com/v1/062cfb070858f437afa2591f462e9cda/aethernet/compat/chat/completions";

const headers = {
  "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`,
  "Content-Type": "application/json"
};

if (process.env.CF_AIG_TOKEN) {
  headers["cf-aig-authorization"] = `Bearer ${process.env.CF_AIG_TOKEN}`;
}

const res = await fetch(url, {
  method: "POST",
  headers,
  body: JSON.stringify({
    model: "openai/gpt-5",
    messages: [
      { role: "user", content: "Say AETHERNet gateway active." }
    ]
  })
});

const text = await res.text();
console.log("STATUS:", res.status);
console.log(text);
