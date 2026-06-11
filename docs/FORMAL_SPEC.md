# Formal System Specification

## Object model

### Claim
A claim is a bounded statement extracted from a transcript, document, or human annotation.

```text
Claim := {claim_id, speaker, text, time_range?, source_id, qualifiers[]}
```

### EvidenceEvent
An evidence event is the atomic unit of the system.

```text
EvidenceEvent := {
  event_id,
  source_id,
  modality,
  feature,
  value,
  confidence in [0,1],
  magnitude in [0,1],
  direction in {supports, refutes, neutral},
  hypothesis_refs[],
  limitations[],
  provenance?
}
```

### Hypothesis
A hypothesis is a falsifiable interpretation over events.

```text
Hypothesis := {
  hypothesis_id,
  label,
  description,
  prior,
  evidence_for[],
  evidence_against[],
  score in [0,1],
  uncertainty in [0,1],
  status,
  alternative_explanations[]
}
```

## Forbidden inference

```text
person_is_liar := forbidden
person_is_guilty := forbidden
single_cue_decision := forbidden
automated_punishment := forbidden
```

## Permitted inference

```text
claim_tension := allowed
verification_pressure := allowed
evidence_gap := allowed
hypothesis_requires_review := allowed
counterevidence_needed := allowed
```

## First-principles target

The system treats human behavior as noisy, multimodal, context-dependent signal, not as a deterministic truth oracle. It optimizes for calibrated structural review, not theatrical certainty.
