"""Independent geometry and exact portfolio settlement checks."""

from fractions import Fraction

import pytest
from sympy import Rational

from roulette.coverage import analyse, european_catalogue
from roulette.rules import AMERICAN_BASKET, RED, straight


def test_catalogue_geometry():
    catalogue = european_catalogue()
    assert {name: len(bets) for name, bets in catalogue.items()} == {
        "straight": 37, "split": 60, "street": 14, "corner": 23,
        "six_line": 11, "dozen": 3, "column": 3, "even_money": 6,
    }
    all_bets = [bet for family in catalogue.values() for bet in family]
    assert len({bet.name for bet in all_bets}) == len(all_bets)
    assert len({bet.numbers for bet in all_bets}) == len(all_bets)
    splits = {bet.numbers for bet in catalogue["split"]}
    assert {(0, 1), (0, 2), (0, 3), (1, 2), (1, 4), (35, 36)} <= splits
    assert (3, 4) not in splits and (0, 4) not in splits
    for a, b in splits - {(0, 1), (0, 2), (0, 3)}:
        assert b - a == 3 or (b - a == 1 and (a - 1) // 3 == (b - 1) // 3)
    for bet in catalogue["corner"]:
        if 0 not in bet.numbers:
            a, b, c, d = bet.numbers
            assert (b, c, d) == (a + 1, a + 3, a + 4) and a % 3 != 0
    assert set(european_catalogue(False)) == {"straight", "split", "street", "corner", "six_line"}


def test_five_disjoint_six_lines():
    bets = european_catalogue()["six_line"][::2][:5]
    result = analyse(bets, [10] * 5)
    assert result.covered_count == result.profitable_count == 30
    assert result.break_even_count == 0 and result.loss_count == 7
    assert result.profitable_probability == Rational(30, 37)
    assert result.distribution == {Rational(-50): Rational(7, 37), Rational(10): Rational(30, 37)}
    assert result.expected_profit == Rational(-50, 37)
    assert result.return_per_unit_staked == Rational(-1, 37)


def test_six_disjoint_lines_only_break_even_on_covered_numbers():
    result = analyse(european_catalogue()["six_line"][::2], [10] * 6)
    assert result.covered_count == result.break_even_count == 36
    assert result.profitable_count == 0 and result.loss_count == 1
    assert result.distribution == {Rational(-60): Rational(1, 37), Rational(0): Rational(36, 37)}


def test_overlap_and_unequal_stakes_separate_coverage_from_profit():
    result = analyse([RED, straight(1)], [1, 10])
    assert result.covered_count == 18 and result.profitable_count == 1
    assert result.profits[1] == 351 and result.profits[3] == -9
    assert result.profits[0] == -11
    assert result.expected_profit == Rational(-11, 37)


def test_fractional_stakes_are_exact():
    result = analyse([straight(0), straight(1), straight(2)], [0.1, "0.2", Fraction(1, 3)])
    assert result.total_stake == Rational(19, 30)
    assert result.expected_profit == Rational(-19, 1110)
    assert all(isinstance(value, Rational) for value in result.profits)
    assert sum(result.distribution.values()) == 1
    assert result.covered_probability == Rational(3, 37)
    assert result.profitable_probability + result.break_even_probability + result.loss_probability == 1
    assert result.best_profit == max(result.profits)
    assert result.worst_profit == min(result.profits)


def test_equal_stake_overlapping_outside_bets():
    red, black, odd, *_ = european_catalogue()["even_money"]
    result = analyse([red, black, odd], [10, 10, 10])
    assert result.covered_count == 36 and result.profitable_count == 18
    assert result.distribution == {
        Rational(-30): Rational(1, 37), Rational(-10): Rational(18, 37),
        Rational(10): Rational(18, 37),
    }
    assert result.expected_profit == Rational(-30, 37)


@pytest.mark.parametrize("stake", [True, 0, -1, float("nan"), float("inf"), "bad", "1/0"])
def test_reject_invalid_stakes(stake):
    with pytest.raises(ValueError):
        analyse([RED], [stake])


def test_invalid_portfolios():
    with pytest.raises(ValueError):
        analyse([])
    with pytest.raises(ValueError):
        analyse([RED], [1, 2])
    with pytest.raises(ValueError):
        analyse([AMERICAN_BASKET])


def test_every_catalogue_bet_matches_independent_fraction_ev():
    for family in european_catalogue().values():
        for bet in family:
            expected = Fraction(len(bet.numbers) * bet.payout - (37 - len(bet.numbers)), 37)
            result = analyse([bet])
            assert result.expected_profit == Rational(expected.numerator, expected.denominator) == Rational(-1, 37)
