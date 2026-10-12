"""Small exhaustive integer allocation oracles and solver status safeguards."""

from itertools import product
from types import SimpleNamespace
from importlib.util import find_spec

import numpy as np
import pytest

from roulette.coverage import analyse, european_catalogue
from roulette.coverage_optimisation import (
    _lattice_certificate, _mod3_minimum_nonzero_support, optimise_coverage,
)
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
    result = optimise_coverage(target_profitable=1, catalogue=(RED,))
    assert result.status == "limit" and result.analysis is None


@pytest.mark.parametrize("status,dual,gap,expected", [
    (1, 0, 1, "limit"), (0, 0, 0.5, "limit"),
    (0, -2, 0, "limit"), (0, 2, 0, "optimal"),
])
def test_numerical_bound_must_reconcile_before_optimal(monkeypatch, status, dual, gap, expected):
    # Full catalogue leaves lattice upper bound-1, whereas two on red lose2.
    catalogue = tuple(bet for family in european_catalogue().values() for bet in family)
    n = len(catalogue)
    vector = np.zeros(2 * n + 38)
    vector[catalogue.index(RED)] = 2
    vector[n + catalogue.index(RED)] = 1
    vector[-1] = -2
    monkeypatch.setattr("roulette.coverage_optimisation.milp", lambda *a, **kw:
                        SimpleNamespace(status=status, success=status == 0, message="mock",
                                        x=vector, fun=2, mip_dual_bound=dual, mip_gap=gap))
    result = optimise_coverage(2, 0, catalogue=catalogue)
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


def test_lattice_rules_out_high_target_for_six_lines_without_solver(monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("analytical impossibility must precede solver")
    monkeypatch.setattr("roulette.coverage_optimisation.milp", unexpected)
    result = optimise_coverage(20, 32, catalogue=european_catalogue()["six_line"])
    assert result.status == "infeasible"
    assert result.lattice_certificate.minimum_required_gross == 32 * 24
    assert result.lattice_certificate.total_gross == 720
    assert result.lattice_certificate.profitable_gross_thresholds[0] is None


def test_lattice_bounds_against_exhaustive_small_allocations():
    candidates = (RED, european_catalogue()["even_money"][1], straight(0))
    gross = [[bet.payout + 1 if pocket in bet.numbers else 0 for bet in candidates]
             for pocket in range(37)]
    for budget in range(1, 7):
        profits_by_count = []
        for stakes in product(range(budget + 1), repeat=3):
            if sum(stakes) == budget:
                profits = [sum(c * x for c, x in zip(row, stakes)) - budget for row in gross]
                profits_by_count.append((sum(p > 0 for p in profits), min(profits)))
        for target in (0, 1, 18, 19, 36, 37):
            bound = _lattice_certificate(gross, budget, target)
            feasible = [floor for count, floor in profits_by_count if count >= target]
            if bound.infeasible:
                assert not feasible
            elif feasible:
                assert max(feasible) <= bound.upper_bound


def test_exact_mod3_residue_enumeration_and_ninety_percent_bound(monkeypatch):
    # Independently enumerate by parity/colour/high-half partitions, not catalogue.
    supports = []
    for coefficients in product(range(3), repeat=6):
        count = 0
        for pocket in range(1, 37):
            indicators = (pocket in RED.numbers, pocket not in RED.numbers,
                          pocket % 2 == 1, pocket % 2 == 0, pocket <= 18, pocket >= 19)
            count += sum(2 * c * int(flag) for c, flag in zip(coefficients, indicators)) % 3 != 0
        supports.append(count)
    assert len(supports) == 729 and supports.count(0) == 9
    assert min(value for value in supports if value) == 16
    assert _mod3_minimum_nonzero_support() == 16
    monkeypatch.setattr("roulette.coverage_optimisation.milp", lambda *a, **kw:
                        SimpleNamespace(status=1, success=False, message="time limit", x=None))
    result = optimise_coverage(20, 34)
    assert result.status == "limit"  # A bound does not establish feasibility.
    assert result.analytical_upper_bound == -20
    assert result.lattice_certificate.mod3_bound_applied


def test_feasibility_mode_returns_exact_witness_without_optimality():
    result = optimise_coverage(5, 19, catalogue=(RED, straight(0)), mode="feasibility")
    assert result.status == "feasible" and result.analysis.profitable_count >= 19
    assert result.optimality_evidence == "exact_feasible_allocation"
    assert result.solver_objective is None and result.solver_dual_bound is None


def test_supplied_incumbent_feasibility_and_bound_attainment(monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("verified witness need not invoke solver")
    monkeypatch.setattr("roulette.coverage_optimisation.milp", unexpected)
    feasible = optimise_coverage(1, 18, catalogue=(RED,), mode="feasibility",
                                 incumbent=((RED,), (1,)))
    assert feasible.status == "feasible" and feasible.incumbent_used
    optimal = optimise_coverage(1, 18, catalogue=(RED,), incumbent=feasible)
    assert optimal.status == "optimal"
    assert optimal.optimality_evidence == "analytical_bound_attained"


def test_incumbent_preserved_and_floor_constrained_after_timeout(monkeypatch):
    bets = european_catalogue()["six_line"][::2][:5]
    def timeout(*args, **kwargs):
        assert kwargs["bounds"].lb[-1] == -20
        return SimpleNamespace(status=1, success=False, message="time limit", x=None)
    monkeypatch.setattr("roulette.coverage_optimisation.milp", timeout)
    result = optimise_coverage(20, 30, incumbent=(bets, (4,) * 5))
    assert result.status == "limit" and result.stakes == (4,) * 5
    assert result.analysis.profitable_count == 30 and result.incumbent_used


@pytest.mark.parametrize("incumbent", [
    ((RED,), (0,)), ((RED,), (1.0,)), ((RED,), (True,)),
    ((RED,), (2,)), ((straight(1),), (1,)), ((RED, RED), (1, 1)),
    ((), ()), ((RED,), (1, 2)), "invalid",
])
def test_reject_invalid_incumbents(incumbent):
    with pytest.raises(ValueError):
        optimise_coverage(1, 18, catalogue=(RED,), incumbent=incumbent)


@pytest.mark.parametrize("kwargs", [{"mode": "bad"}, {"backend": "bad"}])
def test_reject_invalid_modes_and_backends(kwargs):
    with pytest.raises(ValueError):
        optimise_coverage(**kwargs)


def test_missing_cpsat_dependency_is_clear(monkeypatch):
    import builtins
    original = builtins.__import__
    def unavailable(name, *args, **kwargs):
        if name.startswith("ortools"):
            raise ImportError("mock missing dependency")
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", unavailable)
    with pytest.raises(ImportError, match="optional dependency 'ortools'"):
        optimise_coverage(2, 0, backend="cpsat")


@pytest.mark.skipif(find_spec("ortools") is None, reason="optional OR-Tools is not installed")
@pytest.mark.parametrize("budget,target", [(3, 1), (4, 18), (5, 19)])
def test_cpsat_matches_highs_and_exact_settlement(budget, target):
    candidates = (RED, european_catalogue()["even_money"][1], straight(0))
    highs = optimise_coverage(budget, target, catalogue=candidates, time_limit=3)
    cpsat = optimise_coverage(budget, target, catalogue=candidates, backend="cpsat", time_limit=3)
    assert cpsat.status == highs.status
    assert cpsat.analysis.worst_profit == highs.analysis.worst_profit
    assert cpsat.analysis == analyse(cpsat.bets, cpsat.stakes)


@pytest.mark.skipif(find_spec("ortools") is None, reason="optional OR-Tools is not installed")
def test_cpsat_feasibility_mode():
    result = optimise_coverage(5, 19, catalogue=(RED, straight(0)), backend="cpsat", mode="feasibility")
    assert result.status == "feasible" and result.analysis.profitable_count == 19
