# Scientific Foundation Map

This document maps scientific references to concrete BIVE mechanisms. It does not claim that BIVE is clinically, legally or psychophysiologically validated. That would require datasets, protocols, ethics approval where applicable, independent evaluation and domain review. Machines do not become science because someone stapled a bibliography to a repo. Tragic, but useful to remember.

## Reference-to-system mapping

| Reference | Used for | BIVE mechanism | Forbidden inference |
|---|---|---|---|
| Ekman & Friesen, 1969 | nonverbal leakage as weak cue concept | limitations and multimodal-provenance requirement | automatic deception verdict |
| Vrij, 2008 | pitfalls across verbal, nonverbal and physiological methods | conservative review workflow | one-method lie detection |
| Newman, Pennebaker, Berry & Richards, 2003 | linguistic style as probabilistic signal | text feature extraction and uncertainty | universal truth-from-language |
| Picard, 1997 | affective computing / HCI boundary | human-facing operational console | emotion certainty |
| Kahneman & Tversky, 1974 | judgment bias under uncertainty | alternatives, missing evidence, human review | intuitive certainty from sparse evidence |
| NIST AI RMF 1.0 | AI risk governance | risk boundaries, release evidence, status surfaces | trustworthiness without evidence |
| NIST SSDF SP 800-218 | secure software development | release gates, vulnerability workflow | security by README |
| OWASP API Top 10 2023 | API abuse classes | auth boundary, strict schema, payload limits | public unsafe API defaults |
| WCAG 2.2 | accessible interaction | semantic UI, focus states, status feedback | beauty equals usability |

## Primary machine artifacts

- `src/bive/resources/science_registry.json`
- `scripts/validate_science_registry.py`
- `scripts/dynamic_environment_probe.py`
- `tests/test_science_registry.py`
- `tests/test_science_api_contract.py`
- `tests/test_dynamic_environment_probe.py`
- `/api/v1/system/science-registry`
- `/api/v1/system/science-registry/full`
