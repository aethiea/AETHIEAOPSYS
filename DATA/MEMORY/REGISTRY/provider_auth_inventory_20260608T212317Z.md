# PROVIDER AUTH INVENTORY

Timestamp: 2026-06-08T21:23:17Z
Host: RUBIII
Root: /mnt/h/AETHIEAOPSYS

## Vault Secret Slots
- HCLOUD_TOKEN: MISSING
- CLOUDFLARE_API_TOKEN: MISSING
- CLOUDFLARE_ACCOUNT_ID: MISSING
- CLOUDFLARE_ZONE_ID: MISSING
- GITHUB_TOKEN: MISSING
- GITLAB_TOKEN: MISSING
- HF_TOKEN: MISSING
- OPENAI_API_KEY: MISSING
- OPENROUTER_API_KEY: MISSING
- RUNPOD_API_KEY: MISSING
- ORACLE_CLOUD_CONFIG_FILE: MISSING
- AWS_PROFILE: MISSING
- AETHIEA_GOOGLE_ACCOUNT_EMAIL: PRESENT length=19
- AETHIEA_GMAIL_ACCOUNT: PRESENT length=19
- AETHIEA_GIT_IDENTITY_EMAIL: PRESENT length=19
- AETHIEA_HF_SSH_KEY: PRESENT length=31

## Current Shell Secret-Like Exports
- AEVPS_SSH_KEY: PRESENT length=14
- HCLOUD_TOKEN: PRESENT length=64

## Git
- Git work tree: NO
- user.email: aethieaos@gmail.com

## GitHub CLI
- github.com
-   ✓ Logged in to github.com account aethiea (/home/d_ny5u5/.config/gh/hosts.yml)
-   - Active account: true
-   - Git operations protocol: ssh
-   - Token: gho_************************************
-   - Token scopes: 'admin:public_key', 'gist', 'read:org', 'repo'

## GitLab CLI
- glab: missing

## Hugging Face
- [33mWarning: `huggingface-cli` is deprecated and no longer works. Use `hf` instead.
- [0m
- [90mHint: A new version of huggingface_hub (1.18.0) is available! You are using version 1.16.1.
- To update, run: hf update[0m
- [90mHint: `hf` is already installed! Use it directly.
- [0m
- [90mHint: Examples:
-   hf auth login
-   hf download unsloth/gemma-4-31B-it-GGUF
-   hf upload my-cool-model . .
-   hf models ls --search "gemma"
-   hf repos ls --format json
-   hf jobs run python:3.12 python -c 'print("Hello!")'
-   hf --help
- [0m
- HF SSH key: PRESENT
- HF SSH public key: PRESENT

## Cloudflare / cloudflared
- You can obtain more detailed information for each tunnel with `cloudflared tunnel info <name/uuid>`
- ID                                   NAME            CREATED              CONNECTIONS                        
- d7afd49e-b7ca-4cdd-81ff-66ba2dd8de1c AETHERNet       2026-01-14T16:42:47Z 1xiad03, 1xiad08, 1xiad09, 1xiad19 
- 8b52d381-a5e5-464a-a5cf-67951b475be0 AETHERNet_local 2026-05-24T04:45:19Z                                    
- 02fbfd13-4d69-4c30-ab35-1a62c22b5d31 AETHERPort      2026-05-03T08:59:38Z                                    
- 2f1b94a2-e520-4c1c-a5b6-939d00da016c BAE_004_LABELLA 2026-01-01T22:40:17Z                                    
- fee59bcb-90c6-4eb2-af4f-0d5d49c8eae7 corpus-ssh      2026-02-07T23:51:18Z                                    
- 221ef488-2e5e-4a05-b2fa-3ca5525df8b7 labella         2026-01-01T23:16:47Z                                    
- 2026-06-08T21:23:22Z WRN Your version 2026.5.0 is outdated. We recommend upgrading it to 2026.5.2
- cloudflared credential JSON: PRESENT

## Hetzner / hcloud
- ID          NAME        STATUS    IPV4           IPV6                    PRIVATE NET   DATACENTER   AGE
- 138336699   aevps-001   running   5.161.63.237   2a01:4ff:f4:4e2e::/64   -             ash-dc1      1h
