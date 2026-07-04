"""Mutation-check gate — proves the core tests fail on real defects (A3/A4).

Also proves the gate itself is not decoration: a mutation whose killer test cannot
detect it is correctly reported as a SURVIVOR.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mutation_check as mc  # noqa: E402  (needs scripts/ on sys.path first)


def test_all_critical_mutations_are_killed_on_live_tree() -> None:
    report = mc.run()
    assert report["survivors"] == [], f"undefended invariants: {report['survivors']}"
    assert report["status"] == "PASS"
    assert int(report["killed"]) == int(report["total"]) >= 3  # type: ignore[arg-type]


def test_every_mutation_targets_a_real_source_string() -> None:
    # A mutation whose `old` string is absent is untrustworthy (target drifted).
    for mut in mc._MUTATIONS:
        source = (mc.ROOT / mut.file).read_text(encoding="utf-8")
        assert mut.old in source, f"mutation {mut.id} target not present in {mut.file}"


def test_gate_detects_a_survivor(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # Meta-mutation: force the killer to "pass" (mutant not caught) -> must be a survivor.
    monkeypatch.setattr(mc, "_run_killer", lambda _test: False)
    report = mc.run()
    assert report["survivors"], "the gate failed to flag an undetected mutation"
    assert report["status"] == "FAIL"


def test_source_is_reverted_after_a_mutation_run(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    mut = mc._MUTATIONS[0]
    before = (mc.ROOT / mut.file).read_text(encoding="utf-8")
    monkeypatch.setattr(mc, "_run_killer", lambda _test: True)
    mc._apply(mut)
    after = (mc.ROOT / mut.file).read_text(encoding="utf-8")
    assert before == after, "mutation-check left the source mutated"
