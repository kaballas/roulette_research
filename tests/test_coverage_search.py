"""Independent pocket-by-pocket oracles for the equal-chip subset search."""
from itertools import combinations

import pytest

from roulette.coverage_search import SearchLimitExceeded, combination_count, search_coverage
from roulette.rules import RED, straight


def test_small_catalogue_matches_scalar_exhaustive_oracle():
    bets = (straight(0), straight(1), RED)
    result = search_coverage(bets, max_bets=3, batch_size=2)
    for row in result["results"]:
        k = row["number_of_bets"]
        scalar = []
        for subset in combinations(bets, k):
            profits = [sum(b.payout if pocket in b.numbers else -1 for b in subset)
                       for pocket in range(37)]
            scalar.append(sum(profit > 0 for profit in profits))
        assert row["combinations_searched"] == len(scalar)
        assert row["maximum_profitable_count"] == max(scalar)
        for threshold, counts in row["thresholds"].items():
            assert counts["qualifying_combinations"] == sum(100 * n >= 37 * int(threshold) for n in scalar)
        representative = row["representative"]
        assert sum(representative["profits_by_pocket"]) == -k
        assert representative["profitable_count"] + representative["break_even_count"] + representative["loss_count"] == 37


def test_covered_outcomes_are_not_necessarily_profitable():
    result = search_coverage((RED, straight(2)), max_bets=2)
    representative = result["results"][1]["representative"]
    assert representative["covered_count"] == 19
    assert representative["profitable_count"] == 1
    assert representative["break_even_count"] == 18
    assert representative["loss_count"] == 18


def test_search_budget_refuses_before_enumeration(monkeypatch):
    import roulette.coverage_search as module
    monkeypatch.setattr(module, "combinations", lambda *args: pytest.fail("enumeration started"))
    with pytest.raises(SearchLimitExceeded) as exc:
        search_coverage(tuple(straight(i) for i in range(20)), max_bets=10, max_combinations=100)
    assert exc.value.combinations_required == sum(__import__("math").comb(20, k) for k in range(1, 11))


def test_combination_count_and_budget_boundary():
    assert combination_count(11, 10) == 2046
    assert search_coverage((straight(0), straight(1)), max_bets=10, max_combinations=3)["combinations_searched"] == 3
    with pytest.raises(SearchLimitExceeded):
        search_coverage((straight(0), straight(1)), max_combinations=2)


@pytest.mark.parametrize("kwargs", [{"max_bets": 0}, {"max_bets": 1.5}, {"max_combinations": 0},
                                    {"batch_size": 0}])
def test_invalid_search_bounds(kwargs):
    with pytest.raises(ValueError):
        search_coverage((straight(0),), **kwargs)


def test_repeated_bets_rejected():
    with pytest.raises(ValueError, match="distinct"):
        search_coverage((straight(0), straight(0)))


def test_five_nonoverlapping_six_lines_have_thirty_profitable_pockets():
    from roulette.rules import Bet
    bets = tuple(Bet(f"six_line_{start}", tuple(range(start, start + 6)), 5)
                 for start in (1, 7, 13, 19, 25))
    result = search_coverage(bets, max_bets=5)
    representative = result["results"][-1]["representative"]
    assert representative["profitable_count"] == representative["covered_count"] == 30
    assert representative["distribution"] == [
        {"net_profit": -5, "pocket_count": 7, "probability": "7/37"},
        {"net_profit": 1, "pocket_count": 30, "probability": "30/37"}]
    assert representative["expected_profit"] == "-5/37"


def test_batch_boundaries_do_not_change_results():
    bets = tuple(straight(i) for i in range(5))
    assert search_coverage(bets, batch_size=1) == search_coverage(bets, batch_size=7)
