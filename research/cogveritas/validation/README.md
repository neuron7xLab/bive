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

| Metric | In-sample | Held-out (unbiased) |
|---|---|---|
| Language accuracy (overall) | 0.939 [0.894, 0.966] | 0.922 [0.873, 0.953] |
| — English | 1.000 | 1.000 |
| — Ukrainian | 1.000 | 1.000 |
| — Russian | 0.817 [0.701, 0.894] | 0.767 [0.646, 0.856] |
| No-verdict invariant | HOLDS over 383 inputs | (falsification gate) |
| Probability suppression | HOLDS (0 probabilities emitted) | (falsification gate) |
| Integrity | reproducible in-run **and** across `PYTHONHASHSEED` | |
| Verifiability face-validity | 0.875 [0.69, 0.96], n=24 | (sanity check) |

95% Wilson intervals in brackets. Hard invariants are falsification gates — any
violation exits non-zero.

## Known limitation surfaced by this validation

Russian detection is **~77–82%**: every error is `ru → uk`. Root cause: short
Cyrillic sentences that carry none of the orthography-unique letters (ы/э/ъ/ё vs
і/ї/є/ґ), no listed function word, and no `-л/-в` masculine-past marker default to
Ukrainian (the product's Ukrainian-facing default).

A morphological `-ть`/`-шь` rule was prototyped and **rejected**: Ukrainian present
tense (`проводить`, `керують`) and `-ість` nouns (`кількість`) also end in `-ть`, so
the rule regressed Ukrainian (100% → 98%) on held-out data for a small Russian gain.
Tuning on the observed failures would be test-set leakage. The honest fix is a
statistical char-n-gram language identifier (or explicit language selection for
Cyrillic testimony); a heuristic cannot cleanly separate short uk/ru text.
Ukrainian and Russian anchor sets overlap heavily, so a misroute degrades gracefully
rather than fabricating a verdict.
