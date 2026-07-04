from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Real per-gate wall-time for the FULL battery — the resource-effectiveness gate's
# evidence (gates.json is only the 4-gate evidence bundle, not this).
TIMINGS = ROOT / "artifacts" / "verification" / "RELEASE_TIMINGS.json"
LOG = ROOT / "artifacts" / "verification" / "VERIFY_RELEASE.log"


@dataclass(frozen=True)
class GateCommand:
    name: str
    command: list[str]
    timeout_seconds: int = 240


COMMANDS: tuple[GateCommand, ...] = (
    GateCommand("repo-clean", [sys.executable, "scripts/check_repo_clean.py"], 60),
    GateCommand("environment", [sys.executable, "scripts/check_environment.py"], 60),
    GateCommand("metadata", [sys.executable, "scripts/validate_metadata.py"], 60),
    GateCommand("compile", [sys.executable, "-m", "compileall", "-q", "src", "scripts", "tests"], 120),
    GateCommand("dependency-contracts", [sys.executable, "scripts/validate_dependency_contracts.py"], 60),
    GateCommand("test-architecture", [sys.executable, "scripts/validate_test_architecture.py"], 60),
    GateCommand("automation-contract", [sys.executable, "scripts/validate_automation_contract.py"], 60),
    GateCommand("bibliography", [sys.executable, "scripts/validate_bibliography.py"], 60),
    GateCommand("threat-model", [sys.executable, "scripts/validate_threat_model.py"], 60),
    GateCommand("operational-excellence", [sys.executable, "scripts/validate_operational_excellence.py"], 60),
    GateCommand("aos-kernel", [sys.executable, "scripts/validate_aos_kernel.py"], 60),
    GateCommand("cognitive-control", [sys.executable, "scripts/validate_cognitive_control_plane.py"], 60),
    GateCommand("neurocognitive-protocol", [sys.executable, "scripts/validate_neurocognitive_protocol.py"], 60),
    GateCommand("product-readiness", [sys.executable, "scripts/validate_product_operating_model.py"], 60),
    GateCommand("microsoft-rest", [sys.executable, "scripts/validate_microsoft_rest_contract.py"], 60),
    GateCommand("lint", ["ruff", "check", "src", "tests", "scripts"], 120),
    GateCommand("typecheck", [sys.executable, "-m", "mypy", "--no-incremental", "src"], 180),
    GateCommand(
        "coverage",
        [sys.executable, "-m", "pytest", "-p", "pytest_cov", "-m", "not slow", "--cov=bive", "--cov-report=term-missing", "--cov-fail-under=80"],
        240,
    ),
    GateCommand("api-smoke", [sys.executable, "scripts/api_smoke.py"], 120),
    GateCommand("dependency-audit", [sys.executable, "scripts/dependency_audit.py"], 240),
    GateCommand("pr-check", [sys.executable, "scripts/pr_check.py", "--repo", "."], 120),
    GateCommand("schema", [sys.executable, "scripts/validate_schemas.py", "--strict", "--instances"], 120),
    GateCommand("ui-check", [sys.executable, "scripts/check_ui_assets.py"], 60),
    GateCommand("frontend-quality", [sys.executable, "scripts/check_frontend_quality.py"], 60),
    GateCommand("science-registry", [sys.executable, "scripts/validate_science_registry.py"], 60),
    GateCommand("dynamic-probe", [sys.executable, "scripts/dynamic_environment_probe.py"], 120),
    GateCommand("openapi", [sys.executable, "scripts/export_openapi.py", "--output", "docs/openapi.json", "--check"], 120),
    GateCommand("security-static", ["bandit", "-q", "-r", "src", "scripts", "-c", "pyproject.toml", "-ll"], 120),
    GateCommand("wheel-smoke", [sys.executable, "scripts/wheel_smoke.py"], 180),
    GateCommand("manifest-check", [sys.executable, "scripts/validate_release_manifest.py"], 60),
    GateCommand("cogveritas-no-verdict", [sys.executable, "scripts/cogveritas_gates.py", "no-verdict"], 60),
    GateCommand("cogveritas-subject-auc", [sys.executable, "scripts/cogveritas_gates.py", "subject-auc"], 60),
    GateCommand("cogveritas-calibration-ece", [sys.executable, "scripts/cogveritas_gates.py", "calibration-ece"], 60),
    GateCommand("cogveritas-bias-baseline", [sys.executable, "scripts/cogveritas_gates.py", "bias-baseline"], 60),
    GateCommand("cogveritas-artifacts", [sys.executable, "scripts/cogveritas_gates.py", "artifact-manifest"], 60),
    GateCommand("product-claim-audit", [sys.executable, "scripts/product_claim_audit.py"], 60),
    GateCommand("benchmark-card", [sys.executable, "scripts/benchmark_card.py"], 60),
    GateCommand("reference-result-integrity", [sys.executable, "scripts/reference_result_integrity_check.py"], 60),
    GateCommand("contamination-audit", [sys.executable, "scripts/contamination_audit.py"], 60),
    GateCommand("cross-domain-matrix", [sys.executable, "scripts/cross_domain_matrix_check.py"], 60),
    GateCommand("domain-distance", [sys.executable, "scripts/domain_distance_check.py"], 60),
    GateCommand("misuse-threat-model", [sys.executable, "scripts/misuse_threat_model_check.py"], 60),
    GateCommand("external-replication", [sys.executable, "scripts/external_replication_check.py"], 60),
    GateCommand("external-replication-attest", [sys.executable, "scripts/external_replication_attest_check.py"], 60),
    GateCommand("capability-registry", [sys.executable, "scripts/capability_registry_check.py"], 60),
    GateCommand("demo", ["make", "demo"], 120),
    GateCommand("demo-gate", [sys.executable, "-m", "bive.cli", "gate", "--input", "artifacts/local_demo_report.json"], 60),
    GateCommand("evidence-bundle", [sys.executable, "scripts/generate_evidence_bundle.py"], 120),
)


def run_gate(item: GateCommand, env: dict[str, str]) -> tuple[int, str]:
    process = subprocess.Popen(
        item.command,
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    try:
        output, _ = process.communicate(timeout=item.timeout_seconds)
    except subprocess.TimeoutExpired:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
        try:
            output, _ = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            output, _ = process.communicate()
        return 124, (output or "") + f"\nVERIFY_RELEASE_FAIL {item.name} timeout={item.timeout_seconds}s\n"
    return int(process.returncode or 0), output or ""


def main() -> int:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["RUFF_CACHE_DIR"] = str(ROOT / "build" / "ruff-cache")
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    with LOG.open("w", encoding="utf-8") as log:
        log.write(
            "VERIFY_RELEASE Stage 12: repo hygiene, environment preflight, metadata, compile, dependency contracts, "
            "test architecture, automation, bibliography, threat model, Microsoft REST contract, operational excellence, AOS prompt OS kernel, cognitive control plane, neurocognitive protocol, product readiness, lint, typecheck, non-slow coverage, "
            "schemas, API, frontend, science registry, dynamic probe, OpenAPI, static security, "
            "wheel smoke, manifest and evidence bundle. External dependency CVE audit and Docker "
            "runtime remain separate network/host gates.\n"
        )
        timings: list[dict[str, object]] = []
        for item in COMMANDS:
            header = f"\n$ {' '.join(item.command)}\n"
            print(header, end="", flush=True)
            log.write(header)
            log.flush()
            started = time.perf_counter()
            code, output = run_gate(item, env)
            elapsed = round(time.perf_counter() - started, 3)
            timings.append({"name": item.name, "duration_seconds": elapsed, "result": "pass" if code == 0 else "fail"})
            if output:
                print(output, end="", flush=True)
                log.write(output)
            if code != 0:
                msg = f"VERIFY_RELEASE_FAIL {item.name} exit={code}\n"
                print(msg, end="", flush=True)
                log.write(msg)
                _write_timings(timings, "fail")
                return code
            ok = f"VERIFY_GATE_PASS {item.name}\n"
            print(ok, end="", flush=True)
            log.write(ok)
            log.flush()
        print("VERIFY_RELEASE_PASS", flush=True)
        log.write("VERIFY_RELEASE_PASS\n")
    _write_timings(timings, "pass")
    return 0


def _write_timings(timings: list[dict[str, object]], status: str) -> None:
    """Record real per-gate wall-time for the full battery (resource gate's evidence)."""
    total = round(sum(float(t["duration_seconds"]) for t in timings if isinstance(t["duration_seconds"], (int, float))), 3)
    TIMINGS.parent.mkdir(parents=True, exist_ok=True)
    TIMINGS.write_text(
        json.dumps(
            {"gates": timings, "gate_count": len(timings), "total_seconds": total, "status": status},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
