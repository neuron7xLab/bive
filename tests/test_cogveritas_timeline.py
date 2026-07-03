"""Timeline ordering and review-worthy inconsistency flagging."""

from __future__ import annotations

from bive.cogveritas.service import analyze_verifiability
from bive.cogveritas.timeline import build_timeline, detect_conflicts
from bive.cogveritas.verifiability_tagger import analyze


def test_timeline_orders_by_clock_time() -> None:
    _, claims = analyze("О 14:30 я був у банку. О 9:00 я вийшов з дому.")
    tl = build_timeline(claims)
    labels = [t["time_label"] for t in tl]
    assert labels == ["9:00", "14:30"]  # chronological, not source order
    assert all(t["resolved"] for t in tl)


def test_timeline_omits_claims_without_time() -> None:
    _, claims = analyze("Я передав документ. О 10:15 я зустрів свідка.")
    tl = build_timeline(claims)
    assert len(tl) == 1
    assert tl[0]["time_label"] == "10:15"


def test_negation_polarity_conflict_flagged() -> None:
    out = analyze_verifiability("Я передав Петру гроші. Я не передавав Петру жодних грошей.")
    kinds = [c.type for c in out.conflicts]
    assert "negation_polarity" in kinds
    assert out.verdict is None  # a conflict is a pointer, never a verdict


def test_figure_mismatch_conflict_flagged() -> None:
    out = analyze_verifiability("Я заплатив 5000 гривень за оренду. Я заплатив 3000 гривень за оренду.")
    assert any(c.type == "figure_mismatch" for c in out.conflicts)


def test_unrelated_opposite_claims_are_not_conflicts() -> None:
    # Different subjects with opposite polarity must not be flagged.
    conflicts = detect_conflicts(analyze("Я люблю каву вранці. Я не люблю чай ввечері.")[1])
    assert conflicts == []


def test_conflict_quotes_are_verbatim_evidence() -> None:
    out = analyze_verifiability("Він був удома. Він не був удома того вечора.")
    assert out.conflicts
    for c in out.conflicts:
        assert len(c.claim_ids) == 2
        assert len(c.quotes) == 2
