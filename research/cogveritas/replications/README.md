# External replication attestations

Drop a single JSON file here (`<attester>-<date>.json`) to record that you independently
reproduced BIVE's frozen anchored result — the verbal-science headline on the Ott
Deceptive Opinion Spam corpus, frozen in [`../phase0_results.json`](../phase0_results.json)
and pre-registered in [`../phase0_provenance.json`](../phase0_provenance.json).

Your file must conform to
[`schemas/external_replication_attestation.schema.json`](../../../schemas/external_replication_attestation.schema.json).
The gate `scripts/external_replication_attest_check.py` re-derives whether your reported
AUC reproduces the pre-registered value **within its 95% CI**, whether you are genuinely
independent of `neuron7xLab/bive`, and whether a public evidence URL is present. It never
trusts a self-declared "reproduced" flag.

See [`docs/methodology/EXTERNAL_REPLICATION_ATTESTATION.md`](../../../docs/methodology/EXTERNAL_REPLICATION_ATTESTATION.md)
for the full protocol and its honest trust boundary. Only a valid **independent**
attestation lifts the benchmark-grade cap; a `self` attestation is a reproducibility
witness, not a third-party attestation.
