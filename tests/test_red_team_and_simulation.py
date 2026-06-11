from bive.red_team import run_red_team
from bive.simulation import run_simulation


def test_red_team_cases_pass():
    results = run_red_team()
    assert results
    assert all(r.passed for r in results)


def test_simulation_outputs_are_deterministic_enough():
    rows = run_simulation()
    by_name = {r.scenario: r for r in rows}
    assert by_name["pressure_no_check"].status == "review_required"
    assert by_name["calm_verified"].status in {"inconclusive", "low_risk"}
