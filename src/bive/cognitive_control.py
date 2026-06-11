from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from enum import Enum
from importlib import resources

from .aos import (
    AutonomyLevel,
    EvidenceClass,
    OperationalStatus,
    RiskLevel,
    build_execution_contract,
    compile_intent,
    validate_execution_contract,
)


class ControlMode(str, Enum):
    EXECUTE_BOUNDED = "EXECUTE_BOUNDED"
    SPECIFY_ONLY = "SPECIFY_ONLY"
    HUMAN_GATE = "HUMAN_GATE"
    BLOCKED = "BLOCKED"


RISK_PRESSURE: dict[RiskLevel, float] = {
    RiskLevel.LOW: 0.12,
    RiskLevel.MEDIUM: 0.35,
    RiskLevel.HIGH: 0.70,
    RiskLevel.CRITICAL: 0.95,
}

EVIDENCE_SIGNAL: dict[EvidenceClass, float] = {
    EvidenceClass.EXECUTED: 1.00,
    EvidenceClass.SPECIFIED: 0.42,
    EvidenceClass.INFERRED: 0.32,
    EvidenceClass.ASSUMED: 0.18,
    EvidenceClass.UNKNOWN: 0.04,
}


@dataclass(frozen=True)
class CognitiveWeights:
    intent_clarity: float
    evidence_strength: float
    automation_fit: float
    reversibility: float
    dependency_readiness: float
    failure_visibility: float
    risk_pressure: float
    uncertainty_pressure: float
    human_gate_pressure: float
    complexity_pressure: float
    excitation: float
    inhibition: float
    balance_delta: float
    stability_index: float
    closure_score: float

    def to_dict(self) -> dict[str, float]:
        return {
            "intent_clarity": self.intent_clarity,
            "evidence_strength": self.evidence_strength,
            "automation_fit": self.automation_fit,
            "reversibility": self.reversibility,
            "dependency_readiness": self.dependency_readiness,
            "failure_visibility": self.failure_visibility,
            "risk_pressure": self.risk_pressure,
            "uncertainty_pressure": self.uncertainty_pressure,
            "human_gate_pressure": self.human_gate_pressure,
            "complexity_pressure": self.complexity_pressure,
            "excitation": self.excitation,
            "inhibition": self.inhibition,
            "balance_delta": self.balance_delta,
            "stability_index": self.stability_index,
            "closure_score": self.closure_score,
        }


@dataclass(frozen=True)
class AgentVote:
    agent: str
    excitation: float
    inhibition: float
    veto: bool
    rationale: str

    def to_dict(self) -> dict[str, object]:
        return {
            "agent": self.agent,
            "excitation": self.excitation,
            "inhibition": self.inhibition,
            "veto": self.veto,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class FractalCheck:
    level: str
    input_defined: bool
    output_defined: bool
    failure_path_defined: bool
    evidence_required: bool
    human_gate_when_high_risk: bool

    @property
    def passed(self) -> bool:
        return all(
            (
                self.input_defined,
                self.output_defined,
                self.failure_path_defined,
                self.evidence_required,
                self.human_gate_when_high_risk,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "input_defined": self.input_defined,
            "output_defined": self.output_defined,
            "failure_path_defined": self.failure_path_defined,
            "evidence_required": self.evidence_required,
            "human_gate_when_high_risk": self.human_gate_when_high_risk,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class CognitiveControlResult:
    request: str
    mode: ControlMode
    status: OperationalStatus
    autonomy_level: AutonomyLevel
    weights: CognitiveWeights
    agent_votes: tuple[AgentVote, ...]
    fractal_checks: tuple[FractalCheck, ...]
    reverse_inference_plan: tuple[str, ...]
    next_action: str

    def to_dict(self) -> dict[str, object]:
        return {
            "request": self.request,
            "mode": self.mode.value,
            "status": self.status.value,
            "autonomy_level": self.autonomy_level.value,
            "weights": self.weights.to_dict(),
            "agent_votes": [vote.to_dict() for vote in self.agent_votes],
            "fractal_checks": [check.to_dict() for check in self.fractal_checks],
            "reverse_inference_plan": list(self.reverse_inference_plan),
            "next_action": self.next_action,
        }


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def load_cognitive_control_contract() -> dict[str, object]:
    with resources.files("bive.resources").joinpath("cognitive_control_plane.json").open(
        encoding="utf-8"
    ) as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("cognitive control contract must be an object")
    return data


def _intent_clarity(request: str) -> float:
    tokens = [part for part in request.strip().split() if part]
    if not tokens:
        return 0.0
    unique_ratio = len(set(token.lower() for token in tokens)) / max(len(tokens), 1)
    length_signal = min(len(tokens) / 18.0, 1.0)
    return _clamp((0.65 * length_signal) + (0.35 * unique_ratio))


def compute_weights(request: str) -> CognitiveWeights:
    intent = compile_intent(request)
    contract = build_execution_contract(intent)
    contract_errors = validate_execution_contract(contract)
    risk = RISK_PRESSURE[intent.risk_level]
    evidence = EVIDENCE_SIGNAL[intent.evidence_class]
    clarity = _intent_clarity(request)
    human_gate = 1.0 if intent.required_human_gate else 0.0
    reversibility = _clamp(1.0 - (risk * 0.82))
    dependency_readiness = 0.65 if not contract_errors and clarity > 0 else 0.15
    failure_visibility = 0.86 if contract.failure_modes and contract.acceptance_tests else 0.20
    automation_fit = _clamp((0.55 * clarity) + (0.30 * reversibility) + (0.15 * dependency_readiness) - (0.28 * human_gate))
    uncertainty = _clamp((1.0 - clarity) * 0.45 + (1.0 - evidence) * 0.35 + (0.20 if contract_errors else 0.0))
    complexity = _clamp(min(len(request.split()) / 120.0, 1.0) * 0.55 + human_gate * 0.20 + risk * 0.25)
    excitation = _clamp(
        (0.26 * clarity)
        + (0.22 * evidence)
        + (0.18 * automation_fit)
        + (0.15 * reversibility)
        + (0.10 * dependency_readiness)
        + (0.09 * failure_visibility)
    )
    inhibition = _clamp(
        (0.34 * risk)
        + (0.24 * uncertainty)
        + (0.18 * human_gate)
        + (0.14 * complexity)
        + (0.10 * (1.0 - reversibility))
    )
    balance_delta = round(excitation - inhibition, 4)
    stability_index = _clamp(1.0 - abs(balance_delta - 0.18))
    closure_score = _clamp((0.42 * excitation) + (0.26 * evidence) + (0.20 * failure_visibility) + (0.12 * dependency_readiness) - (0.34 * inhibition))
    return CognitiveWeights(
        intent_clarity=clarity,
        evidence_strength=evidence,
        automation_fit=automation_fit,
        reversibility=reversibility,
        dependency_readiness=dependency_readiness,
        failure_visibility=failure_visibility,
        risk_pressure=risk,
        uncertainty_pressure=uncertainty,
        human_gate_pressure=human_gate,
        complexity_pressure=complexity,
        excitation=excitation,
        inhibition=inhibition,
        balance_delta=balance_delta,
        stability_index=stability_index,
        closure_score=closure_score,
    )


def agent_votes(weights: CognitiveWeights, risk: RiskLevel) -> tuple[AgentVote, ...]:
    high_risk = risk in {RiskLevel.HIGH, RiskLevel.CRITICAL}
    return (
        AgentVote("intent_compiler", weights.intent_clarity, weights.uncertainty_pressure, weights.intent_clarity < 0.25, "intent must be explicit before delegation"),
        AgentVote("boundary_detector", weights.reversibility, weights.risk_pressure, high_risk, "irreversible or high-risk actions require gate"),
        AgentVote("contract_engineer", weights.automation_fit, 1.0 - weights.dependency_readiness, weights.dependency_readiness < 0.40, "contract and dependency readiness must be present"),
        AgentVote("verification_engineer", weights.evidence_strength, 1.0 - weights.evidence_strength, weights.evidence_strength < 0.20, "GREEN requires executed evidence"),
        AgentVote("critical_auditor", weights.failure_visibility, weights.complexity_pressure, weights.failure_visibility < 0.50, "failure modes must be visible"),
        AgentVote("repair_optimizer", weights.closure_score, weights.inhibition, weights.closure_score < 0.25, "next patch must improve closure more than complexity"),
    )


def fractal_checks_for_request(request: str) -> tuple[FractalCheck, ...]:
    intent = compile_intent(request)
    contract = build_execution_contract(intent)
    has_input = bool(request.strip())
    has_output = bool(contract.output_schema)
    has_failure = bool(contract.failure_modes)
    evidence_required = any("evidence" in invariant.lower() for invariant in contract.invariants)
    human_gate_ok = not intent.required_human_gate or intent.autonomy_level is AutonomyLevel.L1
    levels = ("intent", "boundary", "contract", "verification", "release")
    return tuple(
        FractalCheck(
            level=level,
            input_defined=has_input,
            output_defined=has_output,
            failure_path_defined=has_failure,
            evidence_required=evidence_required,
            human_gate_when_high_risk=human_gate_ok,
        )
        for level in levels
    )


def reverse_inference_plan(weights: CognitiveWeights, checks: tuple[FractalCheck, ...]) -> tuple[str, ...]:
    actions: list[str] = []
    if weights.evidence_strength < 1.0:
        actions.append("run executable verification gate and attach artifact/log hash")
    if not all(check.passed for check in checks):
        actions.append("repair failing fractal invariant before execution")
    if weights.inhibition > weights.excitation:
        actions.append("reduce risk/ambiguity before increasing autonomy")
    if weights.human_gate_pressure > 0:
        actions.append("obtain explicit human approval before side-effect execution")
    if not actions:
        actions.append("execute bounded workflow and record regression evidence")
    actions.append("recompute cognitive weights after evidence changes")
    return tuple(actions)


def orchestrate_request(request: str) -> CognitiveControlResult:
    intent = compile_intent(request)
    weights = compute_weights(request)
    checks = fractal_checks_for_request(request)
    votes = agent_votes(weights, intent.risk_level)
    vetoed = any(vote.veto for vote in votes)
    if not request.strip():
        mode = ControlMode.BLOCKED
        status = OperationalStatus.UNKNOWN
        next_action = "Provide a concrete request with input, output and boundary."
    elif intent.required_human_gate:
        mode = ControlMode.HUMAN_GATE
        status = OperationalStatus.HUMAN_REVIEW_REQUIRED
        next_action = "Freeze execution; collect approval, rollback and evidence plan."
    elif vetoed or not all(check.passed for check in checks):
        mode = ControlMode.SPECIFY_ONLY
        status = OperationalStatus.YELLOW
        next_action = "Repair contract, evidence or invariant before execution."
    elif weights.excitation >= 0.55 and weights.inhibition <= 0.55:
        mode = ControlMode.EXECUTE_BOUNDED
        status = OperationalStatus.YELLOW
        next_action = "Execute only reversible low-risk steps, then rerun verification gates."
    else:
        mode = ControlMode.SPECIFY_ONLY
        status = OperationalStatus.YELLOW
        next_action = "Specify workflow and collect stronger evidence before automation."
    return CognitiveControlResult(
        request=request,
        mode=mode,
        status=status,
        autonomy_level=intent.autonomy_level,
        weights=weights,
        agent_votes=votes,
        fractal_checks=checks,
        reverse_inference_plan=reverse_inference_plan(weights, checks),
        next_action=next_action,
    )


def cognitive_control_status() -> dict[str, object]:
    contract = load_cognitive_control_contract()
    probe = orchestrate_request("Inspect repository gates and produce reversible remediation plan")
    return {
        "contract": contract,
        "sample_control_result": probe.to_dict(),
        "release_gate": "make cognitive-control",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bive-cognitive-control")
    parser.add_argument("request", nargs="*", help="Request to route through cognitive control plane.")
    args = parser.parse_args(argv)
    request = " ".join(args.request).strip() or "Inspect repository and produce bounded verification plan"
    print(json.dumps(orchestrate_request(request).to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
