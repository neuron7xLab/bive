# Fractal Orchestration Model

Every serious request is checked at five repeated levels:

1. intent
2. boundary
3. contract
4. verification
5. release

Each level must satisfy the same recursive invariants:

- input defined;
- output defined;
- failure path defined;
- evidence required;
- human gate present when risk is HIGH or CRITICAL.

This is called fractal here only in the engineering sense: the same verification structure repeats across different resolution levels. It is not decorative math cosplay.

## Reverse inference

The control plane works backward from target status:

- GREEN requires executed evidence, regression gate, artifact hash and failure-path test;
- YELLOW requires specified contract plus explicit missing runtime evidence;
- BLOCKED requires the blocking dependency and the deterministic unblock action.

The release decision is therefore derived from missing evidence, not from confidence.
