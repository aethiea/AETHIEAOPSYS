# AEVPS CURRENT REGISTRY

Timestamp: 2026-06-09T00:37:56Z
Authority Body: /mnt/h/AETHIEAOPSYS
Host Surface: RUBIII
Provider: Hetzner Cloud

## Server
Name: aevps-001
IPv4: 5.161.63.237
SSH Host Alias: aevps-001

## Cloudflare Tunnel
Tunnel ID: 8b52d381-a5e5-464a-a5cf-67951b475be0
Tunnel Launcher: ~/.local/bin/aevps-tunnel
Service: ~/.config/systemd/user/aevps-tunnel.service

## Doctrine
Operator governs.
AEUSB defines.
RUBIII executes.
Hetzner holds uptime.
Cloudflare routes edge.
Corpus proves.
No host owns.

## Credential Rule
HCLOUD token is host-local and must not be stored in this registry.
SSH private key remains host-local.
AEUSB carries wrappers, routes, receipts, and proof.

## Commands
hcloud-ae location list
hcloud-ae server describe aevps-001
aevps-status
ssh aevps-001
systemctl --user status aevps-tunnel.service
