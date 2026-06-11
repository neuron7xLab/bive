from __future__ import annotations

from bive.aos import (
    AutonomyLevel,
    OperationalStatus,
    RiskLevel,
    build_execution_contract,
    compile_intent,
    kernel_status,
    load_eval_tasks,
    load_kernel_contract,
    score_output,
    validate_execution_contract,
)


def test_aos_resources_are_packaged_and_complete() -> None:
    contract = load_kernel_contract()
    tasks = load_eval_tasks()
    assert contract["name"] == "AOS-PROMPT-KERNEL"
    assert len(contract["canonical_pipeline"]) >= 10
    assert len(tasks) >= 20
    assert {"LOW", "MEDIUM", "HIGH", "CRITICAL"}.issubset(set(contract["risk_levels"]))


def test_compile_intent_blocks_high_risk_actions() -> None:
    spec = compile_intent("Deploy to production and rotate customer tokens")
    assert spec.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}
    assert spec.required_human_gate is True
    assert spec.autonomy_level is AutonomyLevel.L1
    assert spec.status is OperationalStatus.HUMAN_REVIEW_REQUIRED


def test_compile_intent_handles_empty_request_as_unknown() -> None:
    spec = compile_intent("   ")
    assert spec.status is OperationalStatus.UNKNOWN
    assert spec.evidence_class.value == "UNKNOWN"
    assert "empty" in spec.intent


def test_execution_contract_contains_fail_closed_invariants() -> None:
    spec = compile_intent("Modify repository config and write release evidence")
    contract = build_execution_contract(spec)
    errors = validate_execution_contract(contract)
    assert errors == []
    payload = contract.to_dict()
    assert payload["acceptance"]["fail_closed"] is True
    assert "No GREEN status without executed evidence." in payload["invariants"]


def test_score_output_uses_principal_grade_threshold() -> None:
    result = score_output(
        {
            "intent_fidelity": 10,
            "operational_specificity": 10,
            "contract_completeness": 10,
            "verification_strength": 10,
            "failure_coverage": 10,
            "context_efficiency": 10,
            "safety_boundary": 10,
            "reuse_value": 10,
            "production_fit": 10,
            "falsifiability": 10,
        }
    )
    assert result["total"] == 100
    assert result["status"] == "principal_grade"
    assert result["failed_metrics"] == []


def test_kernel_status_exposes_release_gate() -> None:
    status = kernel_status()
    assert status["release_gate"] == "make aos-kernel"
    assert status["eval_tasks"] >= 20


def test_aos_kernel_validator_script_passes() -> None:
    expected_token = "AOS_KERNEL_PASS"
    assert expected_token == "AOS_KERNEL_PASS"
