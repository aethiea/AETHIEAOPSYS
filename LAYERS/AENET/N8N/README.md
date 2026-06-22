# N8N // AENET AUTOMATION LANE

n8n is an automation/workflow surface.

Authority:
- AEUSB carries wrapper, policy, config template, pointer, and receipts.

Memory:
- AEXHB / AE320 carries n8n runtime memory.
- Default memory path is DATA/MEMORY/N8N on the heavy body.

Rules:
- No n8n credentials in Git.
- No webhook secrets in Git.
- No API tokens in Git.
- No hardcoded USB mount path as authority.
- Resolve AEUSB by .aeth_root.
- Resolve AEXHB by heavy-body marker.
