# Operational validation on real open data

Empirical validation of COGVERITAS on a **real, open, labeled** corpus. Run:

```
PYTHONPATH=src python research/cogveritas/validation/validate_operational.py
```

## What this validates — and what it deliberately does not

This validates what the system **actually claims**: language routing, the no-verdict
invariant, probability suppression, integrity reproducibility, and verifiability
face-validity. It does **not** estimate deception-detection accuracy — the system
never emits a deception verdict, and passive verbal deception detection is
empirically at chance (RLT AUC ≈ 0.56, CI straddles chance), so such a metric would
be a category error, not a validation.

## Data (open, reproducible)

- `lang_corpus.json` — 180 sentences (60 uk / 60 ru / 60 en) from **Tatoeba**
  (CC BY 2.0 FR), deterministically selected (dedup, 6–200 chars, sorted by sentence
  id). Gold label = Tatoeba's language tag.
- `lang_heldout.json` — 179 further Tatoeba sentences, **disjoint** from the corpus
  (0 overlap). The held-out figure is the unbiased estimate: the detector was never
  tuned on it.
- `verifiability_probe.json` — 24 curated, hand-labeled factual-vs-opinion exemplars
  for a **face-validity** sanity check (not a population estimate).

## Results (snapshot; re-run to reproduce)

With the char-3-gram language-ID model (`src/bive/cogveritas/lid_model.json`):

| Metric | In-sample | Held-out (unbiased) |
|---|---|---|
| Language accuracy (overall) | 0.994 [0.969, 0.999] | 0.994 [0.969, 0.999] |
| — English | 1.000 | 1.000 |
| — Ukrainian | 1.000 | 1.000 |
| — Russian | 0.983 [0.911, 0.997] | 0.983 [0.911, 0.997] |
| No-verdict invariant | HOLDS over 383 inputs | (falsification gate) |
| Probability suppression | HOLDS (0 probabilities emitted) | (falsification gate) |
| Integrity | reproducible in-run **and** across `PYTHONHASHSEED` | |
| Verifiability face-validity | 0.958 [0.796, 0.992], n=24 | (sanity check) |

95% Wilson intervals in brackets. Hard invariants are falsification gates — any
violation exits non-zero.

## Russian detection: the fix, and the fix that was rejected first

The initial heuristic scored **ru ~77–82%** (held-out): every error was `ru → uk` —
short Cyrillic sentences with none of the orthography-unique letters (ы/э/ъ/ё vs
і/ї/є/ґ), no function-word hit, and no `-л/-в` masculine-past marker defaulted to
Ukrainian.

A morphological `-ть`/`-шь` rule was prototyped and **rejected**: Ukrainian present
tense (`проводить`, `керують`) and `-ість` nouns (`кількість`) also end in `-ть`, so
it regressed Ukrainian on held-out data; tuning on the observed failures would be
test-set leakage.

The shipped fix is a deterministic **char-3-gram naive-Bayes** classifier trained on
the Tatoeba per-language dumps, **disjoint** from both validation corpora (rebuild
with `build_lid_model.py`). It lifts held-out Russian to **0.983** with no Ukrainian
or English regression, and — being pure counts — keeps detection reproducible across
`PYTHONHASHSEED`. The definitive unique-letter checks still short-circuit before the
model.
