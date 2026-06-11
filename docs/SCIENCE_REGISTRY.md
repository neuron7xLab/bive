# Science Registry

BIVE includes a bounded scientific reference registry. Its purpose is not to decorate the repository with impressive names, because apparently that is now a whole industry. Its purpose is to map each scientific domain to concrete engineering constraints, allowed claims, blocked claims and validation tasks.

Canonical machine registry:

```text
src/bive/resources/science_registry.json
```

Review mirror:

```text
data/science/science_registry.json
```

Validation:

```bash
make science-registry
```

## Covered disciplines

- behavioral deception research;
- psychophysiology;
- cognitive science and judgment under uncertainty;
- affective computing and HCI;
- computational linguistics and discourse analysis;
- AI risk governance and secure software engineering;
- accessible operational interface design.

## Hard boundaries

The registry enforces these boundaries:

- no automatic person-level liar label;
- no guilt inference;
- no intent inference;
- no diagnosis;
- no physiology or affect claim without modality-specific data, baselines and confound controls;
- references justify constraints and audit questions, not automatic truth inference.

## Engineering use

| Scientific area | Engineering consequence |
|---|---|
| deception research | output uncertainty, alternatives and human-review questions |
| psychophysiology | require baseline/sensor provenance before physiology claims |
| cognitive science | avoid single-cue certainty and require counter-evidence |
| affective computing | keep UI human-centered and ethically bounded |
| computational linguistics | use text features as weak reviewable evidence only |
| AI risk/security | gate releases, dependency audits, auth, payload limits and provenance |
| accessibility | make the console operable, readable and predictable |
