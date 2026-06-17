# AEUSB CALLABLE AUTH STATUS

Timestamp: 2026-06-16T23:58:13-04:00
Host: RUBIII
User: d_ny5u5
Root: /mnt/h/AETHIEAOPSYS

Doctrine:
  AEUSB is the authority and custody body.
  Host executes.
  AEUSB carries.
  Host does not own.
  No AEUSB means no authenticated callable software.

Custody Roots:
  SSH: /mnt/h/AETHIEAOPSYS/VAULT/AUTH/SSH
  Callable Auth: /mnt/h/AETHIEAOPSYS/VAULT/AUTH/CALLABLE

Installed:
  TOOLIO/bin/aeusb-ssh-authority
  TOOLIO/bin/aeusb-auth-env
  TOOLIO/bin/aeusb-glab-runtime

Receipts:
  DATA/BOOT/AEUSB_CALLABLE_AUTH_CUSTODY_20260616T234215.md
  DATA/BOOT/AEUSB_GLAB_RUNTIME_BRIDGE_*.md

Verified:
  GitHub CLI auth
  GitLab CLI auth
  GitLab SSH
  Cloudflared callable auth lane
  Wrangler callable auth lane

Protected:
  .gitignore contains VAULT/AUTH/
  VAULT/AUTH must never be committed.

Notes:
  /mnt/h reports broad permissions because it is a Windows/USB mount.
  Runtime bridges may copy config into host runtime paths only when a CLI requires Unix permission checks.
