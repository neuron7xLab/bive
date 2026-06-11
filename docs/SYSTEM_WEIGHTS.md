# System Weights

The cognitive control plane exposes operational weights, not psychological labels.

## Excitation signals

- `intent_clarity`
- `evidence_strength`
- `automation_fit`
- `reversibility`
- `dependency_readiness`
- `failure_visibility`

## Inhibition signals

- `risk_pressure`
- `uncertainty_pressure`
- `human_gate_pressure`
- `complexity_pressure`
- `irreversibility`

## Decision modes

- `EXECUTE_BOUNDED`: reversible low-risk action may run with evidence capture.
- `SPECIFY_ONLY`: create contracts and tests before execution.
- `HUMAN_GATE`: human approval required before side effects.
- `BLOCKED`: input or dependency is insufficient.

The balancing target is not maximum excitation. The target is enough excitation to move and enough inhibition to prevent false closure.
