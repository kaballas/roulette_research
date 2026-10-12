"""Small exhaustive integer allocation oracles and solver status safeguards."""

from itertools import product
from types import SimpleNamespace

import numpy as np
import pytest

from roulette.coverage import analyse, european_catalogue
from roulette.coverage_optimisation import optimise_coverage
from roulette.rules import Bet, RED, straight


@pytest.mark.parametrize("budget,target", [(3, 1), (4, 18), (5, 19)])
def test_matches_independent_small_allocation_oracle(budget, target):
    black = european_catalogue()["even_money"][1]
    bets = (RED, black, straight(0))
    feasible = []
    for stakes in product(range(budget + 1), repeat=3):
        if sum(stakes) != budget or sum(value > 0 for value in stakes) > 2:
            continue
        profits = [sum(amount * (bet.payout if pocket in bet.numbers else -1)
                       for amount, bet in zip(stakes, bets)) for pocket in range(37)]
        if sum(value > 0 for value in profits) >= target:
            feasible.append(min(profits))
    result = optimise_coverage(budget, target, max_bets=2, catalogue=bets)
    if not feasible:
        assert result.status == "infeasible" and result.analysis is None
    else:
        assert result.status == "optimal"
        assert result.analysis.worst_profit == max(feasible)
        assert sum(result.stakes) == budget and len(result.bets) <= 2
        assert result.analysis.profitable_count >= target
        assert result.analysis == analyse(result.bets, result.stakes)


def test_uneven_allocations_can_be_required():
    result = optimise_coverage(5, 19, max_bets=2, catalogue=(RED, straight(0)))
    assert result.status == "optimal" and result.stakes in ((4, 1), (3, 2))
    assert result.analysis.profitable_count == 19
    assert result.analysis.worst_profit == -5


def test_impossible_target():
    result = optimise_coverage(2, 37, catalogue=(RED, straight(0)))
    assert result.status == "infeasible"
    assert result.analysis is None and result.stakes == ()


def test_impossible_budget_target_bound():
    result = optimise_coverage(1, 19)
    assert result.status == "infeasible"
    assert result.optimality_evidence == "analytical_infeasibility"
    assert result.analytical_upper_bound == -2


@pytest.mark.parametrize("kwargs", [
    {"budget": True}, {"budget": 0}, {"budget": 1_000_001},
    {"budget": 1.5}, {"target_profitable": -1}, {"target_profitable": 38},
    {"max_bets": 0}, {"max_bets": 11}, {"time_limit": 0},
    {"time_limit": float("nan")}, {"time_limit": float("inf")},
    {"time_limit": True}, {"time_limit": 3601}, {"catalogue": []},
    {"catalogue": [RED, RED]}, {"catalogue": [straight(37)]},
    {"catalogue": [Bet("nonadjacent", (1, 36), 17)]},
])
def test_invalid_requests(kwargs):
    with pytest.raises(ValueError):
        optimise_coverage(**kwargs)


def test_timeout_without_incumbent(monkeypatch):
    monkeypatch.setattr("roulette.coverage_optimisation.milp", lambda *a, **kw:
                        SimpleNamespace(status=1, success=False, message="time limit", x=None))
    result = optimise_coverage(catalogue=(RED,))
    assert result.status == "limit" and result.analysis is None


@pytest.mark.parametrize("status,dual,gap,expected", [
    (1, 0, 1, "limit"), (0, 0, 0.5, "limit"),
    (0, -2, 0, "limit"), (0, 2, 0, "optimal"),
])
def test_numerical_bound_must_reconcile_before_optimal(monkeypatch, status, dual, gap, expected):
    # Two units on red: actual worst-2, analytical upper bound-1 not attained.
    vector = np.r_[2, 1, np.zeros(37), -2]
    monkeypatch.setattr("roulette.coverage_optimisation.milp", lambda *a, **kw:
                        SimpleNamespace(status=status, success=status == 0, message="mock",
                                        x=vector, fun=2, mip_dual_bound=dual, mip_gap=gap))
    result = optimise_coverage(2, 0, catalogue=(RED,))
    assert result.status == expected and result.analysis.worst_profit == -2


def test_exact_bound_certifies_incumbent_after_timeout(monkeypatch):
    monkeypatch.setattr("roulette.coverage_optimisation.milp", lambda *a, **kw:
                        SimpleNamespace(status=1, success=False, message="time limit",
                                        x=np.r_[1, 1, np.zeros(37), -1], fun=1))
    result = optimise_coverage(1, 0, catalogue=(RED,))
    assert result.status == "optimal"
    assert result.analytical_upper_bound == -1
    assert result.optimality_evidence == "analytical_bound_attained"
    assert result.solver_dual_bound is None and result.elapsed_seconds >= 0


def test_invalid_integer_incumbent_rejected(monkeypatch):
    monkeypatch.setattr("roulette.coverage_optimisation.milp", lambda *a, **kw:
                        SimpleNamespace(status=1, success=False, message="mock",
                                        x=np.r_[0.5, 1, np.zeros(37), -1]))
    with pytest.raises(RuntimeError, match="integer allocation"):
        optimise_coverage(1, 0, catalogue=(RED,))
