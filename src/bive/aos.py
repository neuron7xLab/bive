from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from importlib import resources
from typing import Literal, TypedDict


class EvidenceClass(str, Enum):
    EXECUTED = "EXECUTED"
    SPECIFIED = "SPECIFIED"
    INFERRED = "INFERRED"
    ASSUMED = "ASSUMED"
    UNKNOWN = "UNKNOWN"


class OperationalStatus(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    UNKNOWN = "UNKNOWN"
    BLOCKED = "BLOCKED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AutonomyLevel(str, Enum):
    L0 = "L0_MANUAL"
    L1 = "L1_ASSISTED"
    L2 = "L2_SEMI_AUTOMATED"
    L3 = "L3_SUPERVISED_AGENT"
    L4 = "L4_BOUNDED_AUTONOMOUS"
    L5 = "L5_FORBIDDEN_BY_DEFAULT"


ScoreMetricName = Literal[
    "intent_fidelity",
    "operational_specificity",
    "contract_completeness",
    "verification_strength",
    "failure_coverage",
    "context_efficiency",
    "safety_boundary",
    "reuse_value",
    "production_fit",
    "falsifiability",
]


class ScoreBreakdown(TypedDict):
    intent_fidelity: int
    operational_specificity: int
    contract_completeness: int
    verification_strength: int
    failure_coverage: int
    context_efficiency: int
    safety_boundary: int
    reuse_value: int
    production_fit: int
    falsifiability: int


class ScoreResult(TypedDict):
    total: int
    status: str
    failed_metrics: list[str]


@dataclass(frozen=True)
class IntentSpec:
    raw_request: str
    intent: str
    risk_level: RiskLevel
    autonomy_level: AutonomyLevel
    required_human_gate: bool
    evidence_class: EvidenceClass
    status: OperationalStatus
    next_action: str

    def to_dict(self) -> dict[str, object]:
        return {
            "raw_request": self.raw_request,
            "intent": self.intent,
            "risk_level": self.risk_level.value,
            "autonomy_level": self.autonomy_level.value,
            "required_human_gate": self.required_human_gate,
            "evidence_class": self.evidence_class.value,
            "status": self.status.value,
            "next_action": self.next_action,
        }


@dataclass(frozen=True)
class ExecutionContract:
    component_name: str
    intent: str
    input_schema: str
    output_schema: str
    timeout_sec: int
    max_retries: int
    risk_level: RiskLevel
    autonomy_level: AutonomyLevel
    invariants: tuple[str, ...]
    failure_modes: tuple[str, ...]
    acceptance_tests: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "component": {
                "name": self.component_name,
                "role": "bounded automation component",
                "autonomy_level": self.autonomy_level.value,
            },
            "input": {"schema": self.input_schema, "validation": "required"},
            "output": {"schema": self.output_schema, "evidence_required": True},
            "execution": {
                "timeout_sec": self.timeout_sec,
                "max_retries": self.max_retries,
                "idempotent": True,
            },
            "invariants": list(self.invariants),
            "failure_modes": list(self.failure_modes),
            "security": {
                "risk_level": self.risk_level.value,
                "human_gate": self.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL},
            },
            "acceptance": {"tests": list(self.acceptance_tests), "fail_closed": True},
        }


RISK_KEYWORDS: dict[RiskLevel, tuple[str, ...]] = {
    RiskLevel.CRITICAL: (
        "credential",
        "secret",
        "legal",
        "medical",
        "financial",
        "delete all",
        "destroy",
        "public release",
        "production deploy",
    ),
    RiskLevel.HIGH: (
        "send",
        "email",
        "deploy",
        "delete",
        "permission",
        "customer",
        "user data",
        "database",
        "token",
    ),
    RiskLevel.MEDIUM: ("write", "modify", "config", "api", "file", "repository"),
    RiskLevel.LOW: ("read", "summarize", "inspect", "audit"),
}


def classify_risk(text: str) -> RiskLevel:
    normalized = text.lower()
    for level in (RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM):
        if any(keyword in normalized for keyword in RISK_KEYWORDS[level]):
            return level
    return RiskLevel.LOW


def compile_intent(raw_request: str) -> IntentSpec:
    cleaned = " ".join(raw_request.strip().split())
    risk = classify_risk(cleaned)
    human_gate = risk in {RiskLevel.HIGH, RiskLevel.CRITICAL}
    if not cleaned:
        return IntentSpec(
            raw_request=raw_request,
            intent="UNKNOWN: empty request cannot be converted into execution.",
            risk_level=RiskLevel.LOW,
            autonomy_level=AutonomyLevel.L0,
            required_human_gate=False,
            evidence_class=EvidenceClass.UNKNOWN,
            status=OperationalStatus.UNKNOWN,
            next_action="Provide a concrete task input.",
        )
    autonomy = AutonomyLevel.L1 if human_gate else AutonomyLevel.L2
    status = OperationalStatus.HUMAN_REVIEW_REQUIRED if human_gate else OperationalStatus.YELLOW
    return IntentSpec(
        raw_request=raw_request,
        intent=f"Convert request into bounded workflow: {cleaned}",
        risk_level=risk,
        autonomy_level=autonomy,
        required_human_gate=human_gate,
        evidence_class=EvidenceClass.SPECIFIED,
        status=status,
        next_action="Create execution contract and verification gate before execution.",
    )


def build_execution_contract(intent: IntentSpec, component_name: str = "aos_generated_workflow") -> ExecutionContract:
    failure_modes: tuple[str, ...] = (
        "invalid_input",
        "missing_dependency",
        "permission_denied",
        "timeout",
        "schema_mismatch",
        "insufficient_evidence",
    )
    if intent.required_human_gate:
        failure_modes += ("human_gate_missing",)
    return ExecutionContract(
        component_name=component_name,
        intent=intent.intent,
        input_schema="task_request + constraints + available_tools + permissions",
        output_schema="execution_plan + verification_plan + evidence_bundle + final_status",
        timeout_sec=300 if intent.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL} else 120,
        max_retries=0 if intent.risk_level is RiskLevel.CRITICAL else 1,
        risk_level=intent.risk_level,
        autonomy_level=intent.autonomy_level,
        invariants=(
            "No GREEN status without executed evidence.",
            "No irreversible action without human gate.",
            "Every output claim has evidence_class.",
            "Unknown critical dependency blocks release.",
        ),
        failure_modes=failure_modes,
        acceptance_tests=(
            "validate input schema",
            "validate risk classification",
            "validate failure path",
            "validate evidence bundle",
        ),
    )


def validate_execution_contract(contract: ExecutionContract) -> list[str]:
    errors: list[str] = []
    if contract.timeout_sec <= 0:
        errors.append("timeout_sec must be positive")
    if not contract.invariants:
        errors.append("contract must define invariants")
    if not contract.failure_modes:
        errors.append("contract must define failure modes")
    if not contract.acceptance_tests:
        errors.append("contract must define acceptance tests")
    if contract.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL} and contract.autonomy_level is AutonomyLevel.L4:
        errors.append("high/critical risk cannot default to bounded autonomous execution")
    return errors


def score_output(scores: ScoreBreakdown) -> ScoreResult:
    ordered: tuple[ScoreMetricName, ...] = (
        "intent_fidelity",
        "operational_specificity",
        "contract_completeness",
        "verification_strength",
        "failure_coverage",
        "context_efficiency",
        "safety_boundary",
        "reuse_value",
        "production_fit",
        "falsifiability",
    )
    failed_metrics: list[str] = [str(name) for name in ordered if scores[name] < 9]
    total = sum(scores[name] for name in ordered)
    if total >= 97 and not failed_metrics:
        status = "principal_grade"
    elif total >= 95:
        status = "strong"
    elif total >= 90:
        status = "usable"
    else:
        status = "revise"
    return {"total": total, "status": status, "failed_metrics": failed_metrics}


def load_kernel_contract() -> dict[str, object]:
    with resources.files("bive.resources").joinpath("aos_kernel_contract.json").open(
        encoding="utf-8"
    ) as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("aos kernel contract must be an object")
    return data


def load_eval_tasks() -> list[dict[str, object]]:
    with resources.files("bive.resources").joinpath("aos_eval_tasks.json").open(
        encoding="utf-8"
    ) as fh:
        data = json.load(fh)
    tasks = data.get("tasks") if isinstance(data, dict) else None
    if not isinstance(tasks, list):
        raise ValueError("aos eval tasks must contain a tasks list")
    return [task for task in tasks if isinstance(task, dict)]


def kernel_status() -> dict[str, object]:
    contract = load_kernel_contract()
    tasks = load_eval_tasks()
    pipeline = contract.get("canonical_pipeline")
    risk_levels = contract.get("risk_levels")
    evidence_classes = contract.get("evidence_classes")
    return {
        "name": str(contract["name"]),
        "version": str(contract["version"]),
        "status": str(contract["status"]),
        "pipeline_steps": len(pipeline) if isinstance(pipeline, list) else 0,
        "eval_tasks": len(tasks),
        "risk_levels": risk_levels if isinstance(risk_levels, list) else [],
        "evidence_classes": evidence_classes if isinstance(evidence_classes, list) else [],
        "release_gate": "make aos-kernel",
    }
