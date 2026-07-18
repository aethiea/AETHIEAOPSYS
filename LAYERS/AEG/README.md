# AEG — AEGNOSTIXXX

AEG is the foundational identity-resolution layer. It resolves logical bodies from corroborating evidence before any route, service, layer, or host acts.

AEG emits ephemeral session coordinates. It never turns a mount path, drive letter, host, executor, mirror, or cache into identity or authority.

Primary command:

```bash
python3 LAYERS/AEG/resolve.py --exports
```


## Governed body-marker provisioning

AEG resolution does not invent, infer, or silently repair a body role. Labels and attachment paths may corroborate identity, but they do not create authority.

When an already established `AETHIEAOPSYS` corpus body has a pre-existing `.aeth_root` and topology evidence but lacks `.aeth_role` or `.aeth_surface`, use the explicit provisioner.

Dry-run is the default:

```bash
python3 LAYERS/AEG/provision.py \
  --root "$BODY_ROOT" \
  --role AEUSB
```

Apply an approved AEUSB migration:

```bash
python3 LAYERS/AEG/provision.py \
  --root "$BODY_ROOT" \
  --role AEUSB \
  --apply
```

Apply an approved AEXHD migration:

```bash
python3 LAYERS/AEG/provision.py \
  --root "$BODY_ROOT" \
  --role AEXHD \
  --apply
```

The migration route is intentionally constrained:

- A pre-existing `.aeth_root` is required.
- AEUSB is rejected when heavy-body markers are present.
- AEXHD requires pre-existing heavy-body evidence.
- Existing conflicting role or surface values are rejected.
- The provisioner creates neither `.aeth_root` nor heavy-body topology.
- The provisioner does not create authority.
- Repeated application to a compliant body is idempotent.
- A mount coordinate or drive letter is never treated as body identity.

Live bodies that already contain coherent markers require no apply operation.
