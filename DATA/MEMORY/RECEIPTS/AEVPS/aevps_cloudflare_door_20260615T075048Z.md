# AEVPS CLOUDFLARE DOOR RECEIPT

Timestamp UTC: 2026-06-15T07:50:48Z
Surface: RUBIII
VPS: aevps-001
Tunnel Name: AETHERNet_local
Tunnel ID: 8b52d381-a5e5-464a-a5cf-67951b475be0
Service: aethiea-cloudflared.service

## Cloudflare Tunnel Info
NAME:     AETHERNet_local
ID:       8b52d381-a5e5-464a-a5cf-67951b475be0
CREATED:  2026-05-24 04:45:19.772097 +0000 UTC

CONNECTOR ID                         CREATED              ARCHITECTURE VERSION  ORIGIN IP           EDGE                               
1ba169c8-c79a-495e-84e9-b56d017d9f9a 2026-06-15T07:46:28Z linux_amd64  2026.5.0 2a01:4ff:f4:4e2e::1 1xiad09, 1xiad10, 1xiad12, 1xiad19 

## VPS Service Status
active
● aethiea-cloudflared.service - AETHIEAOPSYS Cloudflare Door - AETHERNet_local
     Loaded: loaded (/etc/systemd/system/aethiea-cloudflared.service; enabled; preset: enabled)
     Active: active (running) since Mon 2026-06-15 07:46:28 UTC; 4min 22s ago
   Main PID: 145312 (cloudflared)
      Tasks: 8 (limit: 9251)
     Memory: 14.7M (peak: 17.2M)
        CPU: 1.049s
     CGroup: /system.slice/aethiea-cloudflared.service
             └─145312 /usr/local/bin/cloudflared tunnel --credentials-file [REDACTED_CREDENTIAL_PATH] run 8b52d381-a5e5-464a-a5cf-67951b475be0

Jun 15 07:46:28 aevps-001 systemd[1]: Started aethiea-cloudflared.service - AETHIEAOPSYS Cloudflare Door - AETHERNet_local.

Doctrine: Host executes. AEUSB carries. VPS breathes. Cloudflare routes the Door. Host does not own.
