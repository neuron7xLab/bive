# Capability Registry

Implements the mandate's PR-7 (registry half). Enforced by
`scripts/capability_registry_check.py` (`CAPABILITY_REGISTRY_PASS`), which writes
`artifacts/verification/CAPABILITY_REGISTRY.json`.

Every capability the product **declares** (in the machine-readable envelope
`bive.cogveritas.capabilities.capabilities_envelope`) must map to a real
implementation module, and every declared **hard limit** must map to an enforcement
mechanism that exists. A capability with no backing code, or a limit with no
enforcement, is an unsupported claim and fails the gate.

## Declared capability → backing module

| capability id | backing |
|---|---|
| verifiability | `verifiability_tagger.py` |
| corroboration_worklist | `worklist.py` |
| interview_questions | `interview.py` |
| timeline · inconsistencies | `timeline.py` |
| cross_witness | `witness.py` |
| entity_index | `entities.py` |
| reality_monitoring | `reality_monitoring.py` |
| case_tracking | `service.py` |
| ingestion | `ingest.py` |
| dossier | `dossier.py` |
| integrity | `integrity.py` |

## Hard limit → enforcement mechanism

| limit keyword | enforced by |
|---|---|
| verdict / probability | `output_contract.py` |
| "not a lie detector" | `scripts/product_claim_audit.py` |
| human-in-the-loop | `capabilities.py` |

## Artifact

`CAPABILITY_REGISTRY.json` lists each capability, its backing module, and whether it
is backed. The gate fails if any declared capability is unbacked or any cited limit
mechanism is missing. This keeps the declared surface and the implemented surface in
agreement — the product cannot advertise a capability it does not have.
