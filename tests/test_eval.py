from bive.eval import evaluate_binary


def test_evaluate_binary_metrics():
    r = evaluate_binary([1, 0, 1, 0], [1, 0, 0, 1])
    assert r.n == 4
    assert r.accuracy == 0.5
    assert r.precision == 0.5
    assert r.recall == 0.5
