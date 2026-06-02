# Host Surface Policy

## Root Rule
AEUSB carries the source body.
Hosts execute work.
No host owns the system.

## AEUSB
Role: source/runtime custody, policy, registry, receipts, routing definitions.
Allowed: scripts, configs, manifests, custody records, source code, deployment definitions.
Avoid: node_modules, npm caches, temp builds, heavy model files, disposable runtime scratch.

## Linux ext4 Build Lane
Role: local build/test lane.
Allowed: node_modules, package-lock.json, SDK experiments, temporary test files.

## Hetzner
Role: always-on VPS / stable host organ.
Allowed: services, dashboards, webhook receivers, sync workers, uptime monitors.
Not allowed: becoming source body.

## RunPod
Role: GPU burst / temporary compute organ.
Allowed: model tests, inference bursts, batch jobs, embeddings, video/image/model workloads.
Not allowed: becoming source body.

## Doctrine
Hostless does not mean no hosts.
It means no host owns the system.
