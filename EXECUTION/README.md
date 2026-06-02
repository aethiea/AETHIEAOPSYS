# EXECUTION

Execution is the output layer of AETHIEA.

It handles:
- production
- automation
- runtime activity
- final outputs

Substructures:
- OUTPUT     → completed artifacts
- PIPELINES  → structured workflows
- JOBS       → queued tasks
- RUNTIME    → active processes
- EXPORTS    → outbound deliverables

This layer operates AFTER:
DATA → CORE → DOMAINS → GCR

Invariant:
Execution must respect GCR alignment before output.

No execution without:
- domain mapping
- GCR zone validation

