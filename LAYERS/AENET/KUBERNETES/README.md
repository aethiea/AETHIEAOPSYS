# AETHIEA Kubernetes Lane

Timestamp UTC: 2026-06-22T04:07:34Z
Host: RUBIII
AEUSB Root: /mnt/h/AETHIEAOPSYS
AEXHD Root: /mnt/i/AETHIEAOPSYS

Layout:
- AEUSB carries thin wrappers, manifests, and Git proof.
- AEXHD carries Kubernetes binary payloads and state.
- Docker daemon remains host execution substrate at /var/run/docker.sock.
- No Kubernetes cluster is created by this install step.

Binaries:
- /mnt/i/AETHIEAOPSYS/TOOLIO/KUBERNETES/bin/kubectl
- /mnt/i/AETHIEAOPSYS/TOOLIO/KUBERNETES/bin/helm
- /mnt/i/AETHIEAOPSYS/TOOLIO/KUBERNETES/bin/kind

State:
- /mnt/i/AETHIEAOPSYS/DATA/MEMORY/KUBERNETES/kube/config
- /mnt/i/AETHIEAOPSYS/DATA/MEMORY/KUBERNETES/helm/cache
- /mnt/i/AETHIEAOPSYS/DATA/MEMORY/KUBERNETES/helm/config
- /mnt/i/AETHIEAOPSYS/DATA/MEMORY/KUBERNETES/helm/data

Rule:
Host executes. AEUSB carries. AEXHD remembers. Host does not own.
