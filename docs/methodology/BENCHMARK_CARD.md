# Benchmark Card

Implements PR-1 / §11 of the COGVERITAS Institutional Level-Up Specification. One
card per benchmark: what it is, how it was split, its provenance, its limitations,
and the contamination controls. Validated by `scripts/benchmark_card.py`
(`BENCHMARK_CARD_PASS`) against the frozen `research/cogveritas/phase0_results.json`.

The governing rule (enforced by `scripts/contamination_audit.py`): **any headline
ROC-AUC ≥ 0.85 is assumed to be leakage until proven to transfer cross-corpus.**

## Benchmark: Ott Deceptive Opinion Spam

- **Size:** 1,600 hotel reviews (800 deceptive MTurk / 800 truthful web).
- **Split:** stratified 5-fold CV, isotonic-calibrated logistic; positive = deceptive.
- **Provenance:** Ott et al., the field's gold-standard low-stakes corpus.
- **Frozen result:** verbal-science AUC **0.7507** [0.7269–0.7742], ECE **0.0239**.
- **Controls:** length-only baseline = 0.497 (chance) proves the signal is not a
  length artifact.
- **Contamination flag:** TF-IDF 1–2gram ceiling = **0.9548** AUC — above the 0.85
  leakage line; labelled a *ceiling*, not a capability, and shown below to collapse
  cross-corpus.
- **Limitation (declared in the artifact):** fold-CV is not author/hotel-independent;
  single-domain (hotel reviews); low-stakes instructed lying.

## Benchmark: Diplomacy (out-of-domain transfer)

- **Use:** cross-corpus transfer test only (Ott → Diplomacy).
- **Frozen result:** verbal-science AUC **0.61**; TF-IDF collapses **0.955 → 0.510
  (chance)** — the contamination proof: high in-domain accuracy that does not
  transfer is leakage, not deception signal.

## Benchmark: Real-Life Trial (real high-stakes)

- **Size:** 121 courtroom transcripts, labelled by verdict.
- **Frozen result:** verbal-science AUC **0.562** [0.46–0.67] — CI straddles chance;
  Op-Spam → RLT transfer **0.548 (chance)**.
- **Meaning:** passive verbal deception detection does not work on real high-stakes
  deception. This is the evidence that bounds every product claim (no verdict).

## Contamination controls (summary)

1. Subject/domain-independent evaluation is the target; fold-CV limitations are
   declared where the split is not subject-independent.
2. Every AUC ≥ 0.85 must be accompanied by a *ceiling*/*leakage*/*cross-corpus*
   qualifier (enforced).
3. Cross-corpus collapse is reported alongside in-domain headlines.
4. Frozen results (`phase0_results.json`) are byte-stable and never silently recomputed.

Full write-up: `docs/EMPIRICAL_VALIDATION.md`, `research/cogveritas/PHASE0_REPORT.md`.
