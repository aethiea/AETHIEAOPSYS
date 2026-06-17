# GITLAB SSH AGENT PERSISTENCE

Timestamp: 2026-06-16T23:04:59-04:00
Host: RUBIII
User: d_ny5u5
Root: /mnt/h/AETHIEAOPSYS

Key:
  Private: ~/.ssh/aethieaos_gitlab_ed25519
  Public: ~/.ssh/aethieaos_gitlab_ed25519.pub

Installed:
  TOOLIO/bin/aegitlab-ssh-agent
  ~/.ssh/config GitLab route
  ~/.bashrc AETHIEA GitLab SSH agent startup hook

Rule:
  Passphrase is not stored.
  Agent route persists per live WSL session.
  On fresh wake, operator may be prompted once.
