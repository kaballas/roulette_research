"""Exact tail mass and candidate-frontier counterexamples."""

from dataclasses import replace
from fractions import Fraction

import pytest

from roulette.coverage import analyse, european_catalogue
from roulette.coverage_risk import candidate_frontier, exact_risk
from roulette.rules import RED, straight


def balanced():
    red, black = european_catalogue()["even_money"][:2]
    return analyse((red, black))


def test_fractional_boundary_atom_is_not_all_tied_observations():
    # One pocket loses 2, the other 36 break even. The worst 10% consists of
    # the loss plus exactly 27/370 of the zero-profit probability mass.
    risk = exact_risk(balanced(), Fraction(1, 10))
    assert risk.expected_shortfall == Fraction(20, 37)
    assert risk.conditional_positive_mean is None
    assert risk.conditional_loss_mean == 2
    assert exact_risk(balanced(), Fraction(1, 37)).expected_shortfall == 2
    assert exact_risk(balanced(), Fraction(1, 100)).expected_shortfall == 2


def test_tail_crosses_multiple_distinct_losses():
    red, black = european_catalogue()["even_money"][:2]
    # Zero loses3, black loses1, red wins1. Two-pocket tail averages3 and1.
    risk = exact_risk(analyse((red, black), (2, 1)), Fraction(2, 37))
    assert risk.expected_shortfall == 2
    assert risk.conditional_positive_mean == 1
    assert risk.conditional_loss_mean == Fraction(21, 19)


def test_full_tail_is_negative_expectation_and_scales_exactly():
    analysis = analyse((RED,), (Fraction(3, 2),))
    risk = exact_risk(analysis, 1)
    assert risk.expected_shortfall == Fraction(3, 74)
    assert risk.conditional_positive_mean == risk.conditional_loss_mean == Fraction(3, 2)
    assert risk.profitable_count == 18 and risk.worst_profit == Fraction(-3, 2)
    assert exact_risk(analysis, "0.05").alpha == Fraction(1, 20)


def test_candidate_frontier_keeps_tradeoffs_and_equal_metric_ties():
    black = european_catalogue()["even_money"][1]
    candidates = {"zero": analyse((straight(0),), (2,)),
                  "red": analyse((RED,), (2,)),
                  "balanced": balanced(),
                  "black": analyse((black,), (2,))}
    # Red/black dominate straight0 on positive frequency, with equal worst
    # loss and ES. Balanced sacrifices wins but reduces ES at a 10% tail.
    assert candidate_frontier(candidates, Fraction(1, 10)) == ("red", "balanced", "black")
    assert candidate_frontier(candidates, Fraction(1, 100)) == ("red", "black")
    assert candidate_frontier({}) == ()


def test_frontier_rejects_incomparable_budgets():
    with pytest.raises(ValueError, match="equal total stakes"):
        candidate_frontier({"one": analyse((RED,)), "two": balanced()})


@pytest.mark.parametrize("alpha", [0, -1, Fraction(101, 100), True, "bad", float("nan"), float("inf")])
def test_rejects_invalid_tail_mass(alpha):
    with pytest.raises(ValueError):
        exact_risk(balanced(), alpha)


def test_rejects_invalid_pocket_vector_and_stake():
    with pytest.raises(ValueError, match="37"):
        exact_risk(replace(balanced(), profits=(0,)))
    with pytest.raises(ValueError, match="positive"):
        exact_risk(replace(balanced(), total_stake=0))
