"""Analyzer pipeline — the composition abstraction that assembles the output."""

from __future__ import annotations

from bive.cogveritas.output_contract import build_output
from bive.cogveritas.pipeline import ANALYZERS, build_context, run_pipeline
from bive.cogveritas.service import analyze_verifiability

_TXT = "Петренко: Я передав Коваленку 5000 гривень 3 березня о 14:30."


def test_registry_is_ordered_and_named() -> None:
    names = [name for name, _ in ANALYZERS]
    assert names == list(dict.fromkeys(names))  # unique
    assert "verifiability" in names and "audit_trail" in names


def test_pipeline_produces_the_required_build_output_keys() -> None:
    ctx = build_context(_TXT)
    kwargs = run_pipeline(ctx)
    # The three positionally-required build_output inputs must always be present.
    for required in ("verifiability_gap", "corroboration_questions", "audit_trail"):
        assert required in kwargs
    # And the assembled output is a valid, verdict-free contract.
    out = build_output(**kwargs)
    assert out.verdict is None


def test_analyzers_own_disjoint_output_keys() -> None:
    # Each analyzer contributes distinct fields — no analyzer silently overwrites
    # another's slice (which would make ordering behaviour-significant).
    ctx = build_context(_TXT)
    seen: set[str] = set()
    for _name, analyzer in ANALYZERS:
        keys = set(analyzer(ctx))
        assert not (keys & seen), f"overlapping output keys: {keys & seen}"
        seen |= keys


def test_context_built_once_matches_service_output() -> None:
    # The thin service path and a hand-run pipeline must agree (no hidden step).
    ctx = build_context(_TXT)
    assembled = build_output(**run_pipeline(ctx))
    via_service = analyze_verifiability(_TXT)
    assert assembled.model_dump(exclude={"integrity"}) == via_service.model_dump(exclude={"integrity"})


def test_multi_speaker_flag_gates_cross_witness() -> None:
    single = build_context("Я був удома весь вечір того дня.")
    multi = build_context("А: Я був удома.\nБ: Він не був удома того вечора.")
    assert single.multi_speaker is False
    assert multi.multi_speaker is True
