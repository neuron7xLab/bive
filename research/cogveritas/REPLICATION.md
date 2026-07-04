# External Replication Package

Implements PR-6 / §? of the COGVERITAS Institutional Level-Up Specification.
Validated by `scripts/external_replication_check.py` (`EXTERNAL_REPLICATION_READY`):
an independent party MUST be able to reproduce the empirical claims from public
data with the assets in this directory.

## Assets (all in `research/cogveritas/`)

| Asset | Role |
|---|---|
| `fetch_data.sh` | download the public corpora (Op-Spam, Diplomacy, RLT) |
| `features.py` | interpretable, cited verbal features (Verifiability Approach, RM, LIWC-style) |
| `evaluate.py` | subject/fold split, isotonic-calibrated logistic, ROC-AUC / ECE / Brier + CIs |
| `leakage_audit.py` | contamination probe (TF-IDF ceiling, cross-corpus collapse, shortcut probe) |
| `rlt_transfer.py` | Op-Spam → Real-Life Trial high-stakes transfer test |
| `phase0_results.json` | frozen headline results (byte-stable; never silently recomputed) |
| `PHASE0_REPORT.md` | full write-up |

## Steps

```bash
cd research/cogveritas
./fetch_data.sh                 # public corpora into ./data (gitignored)
python evaluate.py              # reproduces the in-domain + cross-corpus table
python leakage_audit.py         # reproduces the contamination findings
python rlt_transfer.py          # reproduces the Real-Life Trial (chance-level) result
```

## Expected reproduction

- in-domain (Ott, 5-fold): ROC-AUC ≈ **0.75**, ECE ≈ **0.024**
- TF-IDF ceiling ≈ **0.955** in-domain → **0.510 (chance)** cross-corpus (leakage)
- Real-Life Trial: ROC-AUC ≈ **0.562**, CI straddles chance
- length-only baseline ≈ **0.497** (chance)

The frozen `phase0_results.json` is the reference; a replication that diverges
materially from it indicates an environment or data difference to investigate, not
a new capability claim.

## Environment

Pinned via the repository's `requirements/` lockfiles; the optional research extra
(`numpy`, `scikit-learn`) is declared in `pyproject.toml` (`cogveritas` extra).
Data is not committed (licensing); `fetch_data.sh` obtains it from public sources.
