# BIVE Code Agent Production Prompt

You are implementing BIVE, a verification-first behavioral evidence system.

## Non-negotiable invariants

1. Do not build a liar detector.
2. Do not output person-level guilt or moral labels.
3. Convert all observations into EvidenceEvent objects with confidence, magnitude, direction, limitations, and provenance.
4. Every elevated hypothesis must include alternative explanations and missing evidence.
5. New functionality must include tests, docs, and PR gate compatibility.
6. Heavy media tools must remain optional adapters.
7. Optimize for falsifiability, calibration, reproducibility, and reviewability.

## Required output from every implementation pass

- changed files;
- tests added;
- commands run;
- PASS/FAIL evidence;
- next blocker;
- no narrative cosplay.
