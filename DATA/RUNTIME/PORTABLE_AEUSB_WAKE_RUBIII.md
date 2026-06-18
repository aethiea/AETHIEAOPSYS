# PORTABLE AEUSB WAKE — RUBIII

Status: VERIFIED

Authority rule:
- Select AETHIEAOPSYS only when `.aeth_root` exists.
- Require `STATUS.md`.
- Reject `AE320GB_HEAVY_BODY`.
- Reject `.aeth_heavy_body`.

Windows behavior:
- `%LOCALAPPDATA%\AETHIEA\Start-AETHIEA.ps1` discovers the current AEUSB drive letter at runtime.
- USB port and drive letter are not fixed.
- USB forwarder routes into the stable host bootstrap.

WSL behavior:
- `~/.local/bin/aeth-mount-authority` asks Windows where AEUSB is mounted.
- WSL mounts the current drive letter dynamically.
- Interactive WSL login enters `/mnt/<current-letter>/AETHIEAOPSYS`.
- `aeth_root`, `aeth`, and `aegit` resolve authority dynamically.

Current verified root:
- `/mnt/j/AETHIEAOPSYS`

Doctrine:
- Host executes.
- AEUSB carries.
- Host does not own.
- AE320 is heavy body, not authority.
- DON’T MINGLE.
