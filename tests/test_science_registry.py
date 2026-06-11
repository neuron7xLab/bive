from __future__ import annotations

from bive.science import load_science_registry, science_registry_summary, validate_science_registry


def test_science_registry_is_bounded_and_connected() -> None:
    registry = load_science_registry()

    validate_science_registry(registry)
    assert registry["status"] == "bounded_reference_registry"
    assert len(registry["disciplines"]) >= 7
    assert len(registry["references"]) >= 8
    assert any("must not emit person-level" in boundary for boundary in registry["hard_boundaries"])


def test_science_registry_summary_is_small_contract() -> None:
    summary = science_registry_summary()

    assert summary["registry_id"].startswith("bive-science-registry")
    assert summary["reference_count"] >= 8
    assert all(set(item) == {"id", "name", "operational_use"} for item in summary["disciplines"])
