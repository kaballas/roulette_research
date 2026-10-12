"""Distinct-portfolio explorer: exact settlement, diversity and brute-force oracle."""

from fractions import Fraction
from itertools import combinations
import importlib.util
from pathlib import Path
import sys

import pytest
from sympy import Rational

from roulette.coverage import analyse, european_catalogue
from roulette.coverage_explorer import (
    DEFAULT_FAMILIES, catalogue_for, describe_bet, explore_portfolios, objective_value,
)
from roulette.coverage_risk import exact_risk

ROOT = Path(__file__).resolve().parents[1]


def small_catalogue():
    groups = european_catalogue()
    return (groups["dozen"] + groups["column"] + groups["even_money"][:2]
            + groups["even_money"][4:] + groups["street"][:2] + groups["six_line"][:3])


def compositions(total, parts):
    if parts == 1:
        yield (total,)
        return
    for first in range(1, total - parts + 2):
        for rest in compositions(total - first, parts - 1):
            yield (first, *rest)


def brute_force_values(catalogue, budget, max_bets, target, objective):
    values = []
    for k in range(1, max_bets + 1):
        for bets in combinations(catalogue, k):
            for stakes in compositions(budget, k):
                a = analyse(bets, stakes)
                if a.profitable_count >= target:
                    values.append(objective_value(a, exact_risk(a), objective))
    return sorted(values)


@pytest.mark.parametrize("objective", ["worst_loss", "frequency", "tail"])
def test_best_portfolio_matches_brute_force(objective):
    catalogue = small_catalogue()
    result = explore_portfolios(6, 22, 3, objective, catalogue, count=1, time_limit=60)
    oracle = brute_force_values(catalogue, 6, 3, 22, objective)
    assert result.portfolios
    assert result.portfolios[0].objective_value == oracle[0]


def test_alternatives_are_exact_and_distinct():
    catalogue = small_catalogue()
    result = explore_portfolios(6, 22, 3, "worst_loss", catalogue, count=5,
                                min_distance=2, time_limit=60)
    assert len(result.portfolios) >= 3
    profiles, sets = set(), []
    for p in result.portfolios:
        a = analyse(p.bets, p.stakes)
        assert a == p.analysis and sum(p.stakes) == 6 and len(p.bets) <= 3
        assert a.profitable_count >= 22
        assert a.expected_profit == Rational(-6, 37)
        assert sum(a.profits) == -6
        profiles.add(tuple(sorted(a.profits)))
        sets.append({b.name for b in p.bets})
    assert len(profiles) == len(result.portfolios)
    for left, right in combinations(sets, 2):
        assert len(left ^ right) >= 2
    values = [p.objective_value for p in result.portfolios]
    assert values == sorted(values)
    assert [p.rank for p in result.portfolios] == list(range(1, len(values) + 1))


def test_tail_objective_equals_exact_expected_shortfall():
    result = explore_portfolios(6, 22, 3, "tail", small_catalogue(), count=2, time_limit=60)
    for p in result.portfolios:
        assert p.objective_value == exact_risk(p.analysis, Fraction(1, 20)).expected_shortfall


def test_equal_stake_mode_and_reference_exclusion():
    catalogue = small_catalogue()
    first = explore_portfolios(6, 22, 3, "worst_loss", catalogue, count=1, time_limit=60,
                               stake_mode="equal")
    assert first.portfolios
    for p in first.portfolios:
        assert len(set(p.stakes)) == 1
    best = first.portfolios[0]
    again = explore_portfolios(6, 22, 3, "worst_loss", catalogue, count=2, time_limit=60,
                               stake_mode="equal", min_distance=1, exclude=[best.bets])
    assert all({b.name for b in p.bets} != {b.name for b in best.bets} for p in again.portfolios)


def test_unreachable_target_is_analytically_infeasible():
    result = explore_portfolios(20, 37, 10, "worst_loss", catalogue_for(DEFAULT_FAMILIES),
                                count=3, time_limit=10)
    assert result.portfolios == () and result.stop_reason == "analytical_infeasible"


def test_equal_mode_with_no_divisor_is_infeasible():
    result = explore_portfolios(7, 20, 1, "worst_loss", small_catalogue(), count=1,
                                time_limit=10, stake_mode="equal")
    assert result.stop_reason in ("analytical_infeasible", "exhausted")
    assert not result.portfolios or all(len(set(p.stakes)) == 1 for p in result.portfolios)


@pytest.mark.parametrize("kwargs", [
    {"budget": 0}, {"max_bets": 11}, {"count": 0}, {"objective": "ev"},
    {"stake_mode": "random"}, {"time_limit": float("nan")}, {"min_distance": 0},
    {"target_profitable": 38}, {"alpha": 0},
])
def test_invalid_inputs_rejected(kwargs):
    with pytest.raises(ValueError):
        explore_portfolios(**{"budget": 6, "target_profitable": 20, "max_bets": 3,
                              "catalogue": small_catalogue(), **kwargs})


def test_catalogue_rejects_unknown_family_and_non_physical_bets():
    with pytest.raises(ValueError):
        catalogue_for(["pentagon"])
    from roulette.rules import Bet
    with pytest.raises(ValueError):
        explore_portfolios(6, 20, 3, catalogue=(Bet("fake", (1, 2, 5), 11),))


def test_describe_bet_labels():
    groups = european_catalogue()
    assert describe_bet(groups["split"][0]) == "Split 1/2"
    assert describe_bet(groups["six_line"][0]) == "Six-line 1-6"
    assert describe_bet(groups["dozen"][1]) == "Dozen 13-24"
    assert describe_bet(groups["even_money"][4]) == "Low 1-18"


@pytest.fixture
def cli(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "experiments"))
    spec = importlib.util.spec_from_file_location(
        "explore_combinations_cli", ROOT / "experiments/explore_combinations.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_reference_loader_finds_recorded_34_of_37(cli):
    path = ROOT / "results" / "coverage-benchmark-060.json"
    if not path.exists():
        pytest.skip("recorded benchmark evidence absent")
    catalogue = catalogue_for(DEFAULT_FAMILIES)
    ref = cli.load_references([path], catalogue, 20, 10, 34)
    assert ref is not None
    a = analyse(ref.bets, ref.stakes)
    assert a.profitable_count == 34 and a.worst_profit == -20 and a.total_stake == 20
    assert cli.load_references([path], catalogue, 30, 10, 34) is None


def test_cell_row_and_markdown_have_all_37_pockets(cli):
    catalogue = small_catalogue()
    result = explore_portfolios(6, 22, 3, "worst_loss", catalogue, count=2, min_distance=2,
                                time_limit=60)
    task = (6, 3, 60, "worst_loss", "any", ["dozen"], 2, 2, 60, None)
    cell = cli.cell_row(task, result, None, None)
    assert cell["returned"] == len(result.portfolios)
    for row in cell["portfolios"]:
        assert len(row["profit_by_number"]) == 37
        assert row["return_per_chip"] == "-1/37"
    text = cli.markdown({"cells": [cell]})
    assert "| Combination |" in text and "36:" in text


@pytest.mark.parametrize("stake_mode", ["any", "equal"])
@pytest.mark.parametrize("alpha", [Fraction(1, 19), Fraction(2, 37), Fraction(1, 2)])
def test_tail_matches_brute_force_for_other_alpha(alpha, stake_mode):
    catalogue = small_catalogue()[:8]
    result = explore_portfolios(6, 20, 3, "tail", catalogue, count=1, time_limit=60,
                                alpha=alpha, stake_mode=stake_mode)
    best = None
    for k in (1, 2, 3):
        for bets in combinations(catalogue, k):
            for stakes in compositions(6, k):
                if stake_mode == "equal" and len(set(stakes)) != 1:
                    continue
                a = analyse(bets, stakes)
                if a.profitable_count >= 20:
                    value = exact_risk(a, alpha).expected_shortfall
                    best = value if best is None or value < best else best
    assert result.portfolios[0].objective_value == best


def test_unrepresentable_alpha_rejected():
    with pytest.raises(ValueError):
        explore_portfolios(6, 20, 3, "tail", small_catalogue(), alpha=Fraction(1, 10**400))


def _write_reference(tmp_path, rows):
    import json
    path = tmp_path / "ref.json"
    path.write_text(json.dumps({"results": rows}))
    return path


def _row(bets, stakes):
    return {"bets": [{"name": b.name, "numbers": list(b.numbers), "payout": b.payout}
                     for b in bets], "stakes": stakes}


def test_reference_follows_objective_and_stake_mode(cli, tmp_path):
    groups = european_catalogue()
    catalogue = catalogue_for(DEFAULT_FAMILIES)
    lows = (groups["even_money"][4], groups["even_money"][5])
    dozens = groups["dozen"]
    mixed = _row(lows + (dozens[0],), [7, 7, 4])
    equal = _row(dozens, [6, 6, 6])
    path = _write_reference(tmp_path, [mixed, equal])
    a_mixed = analyse(lows + (dozens[0],), [7, 7, 4])
    a_equal = analyse(dozens, [6, 6, 6])
    chosen = cli.load_references([path], catalogue, 18, 10, 0, "worst_loss", "equal")
    assert chosen is not None and len(set(chosen.stakes)) == 1
    for objective in ("frequency", "worst_loss", "tail"):
        got = cli.load_references([path], catalogue, 18, 10, 0, objective, "any")
        values = {
            name: objective_value(a, exact_risk(a), objective)
            for name, a in (("m", a_mixed), ("e", a_equal))
        }
        if values["m"] == values["e"]:
            continue
        winner = "m" if values["m"] < values["e"] else "e"
        assert (len(set(got.stakes)) == 1) == (winner == "e")


def test_reference_exclusion_uses_physical_identity(cli):
    catalogue = small_catalogue()
    renamed = [type(b)("alias_" + b.name, b.numbers, b.payout) for b in catalogue[:3]]
    task = (6, 3, 60, "worst_loss", "any", ["dozen", "column", "even_money"], 1, 1, 30,
            {"keys": [(sorted(b.numbers), b.payout) for b in renamed]})
    _, result = cli.run_cell(task)
    assert all({b.name for b in p.bets} != {b.name for b in catalogue[:3]}
               for p in result.portfolios)
    task = task[:-1] + ({"keys": [([5, 6, 7], 11)]},)
    with pytest.raises(ValueError):
        cli.run_cell(task)


def test_frequency_descends_levels_instead_of_stopping_on_twins():
    catalogue = small_catalogue()
    result = explore_portfolios(6, 10, 3, "frequency", catalogue, count=6, min_distance=1,
                                time_limit=60)
    assert len(result.portfolios) >= 2
    for p in result.portfolios:
        assert p.analysis.profitable_count == sum(1 for v in p.analysis.profits if v > 0)
    profiles = {tuple(sorted(p.analysis.profits)) for p in result.portfolios}
    assert len(profiles) == len(result.portfolios)


def test_frequency_best_matches_brute_force_after_exact_indicator():
    catalogue = small_catalogue()
    result = explore_portfolios(6, 22, 3, "frequency", catalogue, count=3, time_limit=60)
    oracle = brute_force_values(catalogue, 6, 3, 22, "frequency")
    assert result.portfolios[0].objective_value == oracle[0]
