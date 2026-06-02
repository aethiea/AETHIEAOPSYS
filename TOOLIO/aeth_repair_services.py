#!/usr/bin/env python3
import subprocess
services = ["aeth-portal", "cloudflared", "aeth-cloud-sync"]
for s in services:
    print("RESTART →", s)
    subprocess.run(["sudo", "systemctl", "restart", s])
subprocess.run(["systemctl", "status", *services, "--no-pager"])
