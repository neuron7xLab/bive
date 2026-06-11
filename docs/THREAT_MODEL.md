# Microsoft SDL-Oriented Threat Model

This repository carries a machine-verifiable threat model in `data/security/stride_threat_model.json`.

The model contains:

- explicit protected assets;
- trust boundaries;
- DFD-style data flows;
- STRIDE coverage for Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service and Elevation of Privilege;
- mitigation and verification command for every listed threat.

Release gate:

```bash
make threat-model
```

The threat model is not a compliance ornament. If a boundary, API behavior, storage path, dependency surface or scientific claim boundary changes, the JSON model and this document must change in the same PR.
