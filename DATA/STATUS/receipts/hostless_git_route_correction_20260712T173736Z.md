# AETHIEAOPSYS — HOSTLESS GIT ROUTE CORRECTION

Timestamp UTC: 2026-07-12T17:37:36Z

## Read

Hostless root resolution worked.

Resolved corpus body:

/mnt/k/AETHIEAOPSYS

The failed command was:

git -C "$ROOT"

That failed because the resolved corpus body is not a normal .git worktree.

## Correct Git Route

Use:

git --git-dir="/home/d_ny5u5/.aethiea_git/AETHIEAOPSYS.git" --work-tree="/mnt/k/AETHIEAOPSYS"

## Lock

Hostless resolves the body.
Bare Git seals the body.
No mount path becomes authority.
No host owns the OS.
