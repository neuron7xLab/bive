# External Replication Guide

Implements the mandate's PR-6. Validated by `scripts/external_replication_check.py`
(`EXTERNAL_REPLICATION_READY`), which writes
`artifacts/verification/EXTERNAL_REPLICATION_READINESS.json`.

An independent party MUST be able to reproduce the empirical claims from public data.
This guide is the human-readable entry point; the frozen assets and steps live in
`research/cogveritas/` (see `research/cogveritas/REPLICATION.md`).

## Fresh-environment reproduction

```bash
git clone https://github.com/neuron7xLab/bive && cd bive
python -m venv .venv && . .venv/bin/activate
python -m pip install -e ".[dev,api,security]" -e ".[cogveritas]"
cd research/cogveritas
./fetch_data.sh          # public corpora into ./data (gitignored, licensing)
python evaluate.py       # in-domain + cross-corpus table
python leakage_audit.py  # contamination findings (TF-IDF ceiling / collapse)
python rlt_transfer.py   # Real-Life Trial (chance-level) result
```

## Expected reproduction (reference: `phase0_results.json`)

- in-domain (Ott, 5-fold): ROC-AUC ≈ **0.75**, ECE ≈ **0.024**
- TF-IDF ceiling ≈ **0.955** in-domain → **0.510 (chance)** cross-corpus (leakage)
- Real-Life Trial: ROC-AUC ≈ **0.562** (CI straddles chance)
- length-only baseline ≈ **0.497** (chance)

## Fail-closed on unavailable data

`fetch_data.sh` obtains data from public sources; it is not committed (licensing). If
a corpus is unavailable, reproduction is **blocked, not silently skipped** — a partial
run is not a success. The readiness gate checks the package is complete (assets +
frozen reference + documented steps); it does not fake having reproduced results the
runner did not compute.

## Boundary

`EXTERNAL_REPLICATION_READY` means the *package is ready for* independent replication.
It does **not** assert that a third party *has* replicated. The institutional
scorecard caps maturity below benchmark-grade until an actual external replication is
recorded.
