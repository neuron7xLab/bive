# Neurocognitive Feature Map

This document defines CNS-inspired repository features only as operational engineering analogies.
It does not claim biological identity, diagnosis, deception detection, guilt inference or mental-state inference.

## Executable mapping

| Feature | Operational function | Runtime mechanism | Validator |
| --- | --- | --- | --- |
| excitation/inhibition balance | move only when evidence, reversibility and readiness outrun risk | `src/bive/cognitive_control.py` | `make cognitive-control` |
| salience gating | prioritize risk/evidence/failure signals over emotional intensity | agent votes + feature map | `make neurocognitive-protocol` |
| working-memory budget | compress task into intent contract, execution graph and artifact | AOS response contract | `make aos-kernel` |
| error monitoring | find fake readiness and missing evidence | adversarial verifier + release gates | `make test-architecture` |
| predictive reverse inference | backcast from target status to missing evidence | `reverse_inference_plan()` | `make cognitive-control` |
| homeostatic stability | keep control variables inside safe ranges | `weight_bounds` | `make cognitive-control` |
| fractal invariant recursion | repeat same invariant across intent/boundary/contract/verification/release | fractal checks | `make cognitive-control` |
| plasticity calibration | patch only from measured eval failure | AOS eval harness | `make aos-kernel` |

## Rule

A neurocognitive term is allowed only if it maps to a repository mechanism, validator, test and failure mode.
