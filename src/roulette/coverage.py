"""Exact one-spin portfolios on a fair, standard single-zero European wheel.

The catalogue uses the three-column layout and zero-area convention in Crown
Melbourne Roulette Rules v19, sections 6.1–6.3 (10 April 2026). It does not model
French concessions, table limits, chip denominations or racetrack call bets.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from sympy import Rational

from roulette.rules import Bet, RED, Wheel, validate_bet


def european_catalogue(include_outside: bool = True) -> dict[str, tuple[Bet, ...]]:
    """Return physical-layout bets, grouped by family in deterministic order.

    Zero trios belong to ``street`` and first-four belongs to ``corner``.
    Six-lines join successive numbered streets, excluding the zero trios.
    """
    def bet(family: str, numbers: Iterable[int]) -> Bet:
        covered = tuple(numbers)
        return Bet(f"{family}_{'_'.join(map(str, covered))}", covered,
                   36 // len(covered) - 1)

    families = {
        "straight": tuple(bet("straight", (n,)) for n in range(37)),
        "split": tuple(
            [bet("split", (n, n + 1)) for n in range(1, 37) if n % 3]
            + [bet("split", (n, n + 3)) for n in range(1, 34)]
            + [bet("split", (0, n)) for n in (1, 2, 3)]),
        "street": tuple(
            [bet("street", range(n, n + 3)) for n in range(1, 35, 3)]
            + [bet("street", (0, 1, 2)), bet("street", (0, 2, 3))]),
        "corner": tuple(
            [bet("corner", (n, n + 1, n + 3, n + 4))
             for n in range(1, 33) if n % 3]
            + [bet("corner", (0, 1, 2, 3))]),
        "six_line": tuple(bet("six_line", range(n, n + 6))
                          for n in range(1, 32, 3)),
    }
    if include_outside:
        families.update({
            "dozen": tuple(bet("dozen", range(n, n + 12)) for n in (1, 13, 25)),
            "column": tuple(bet("column", range(n, 37, 3)) for n in (1, 2, 3)),
            "even_money": (
                RED, Bet("black", tuple(n for n in range(1, 37)
                                         if n not in RED.numbers), 1),
                Bet("odd", tuple(range(1, 37, 2)), 1),
                Bet("even", tuple(range(2, 37, 2)), 1),
                Bet("low", tuple(range(1, 19)), 1),
                Bet("high", tuple(range(19, 37)), 1),
            ),
        })
    return families


@dataclass(frozen=True)
class CoverageAnalysis:
    """Exact portfolio net profit; coverage differs from positive total profit."""

    total_stake: Rational
    profits: tuple[Rational, ...]
    covered_count: int
    profitable_count: int
    break_even_count: int
    loss_count: int
    expected_profit: Rational
    return_per_unit_staked: Rational
    worst_profit: Rational
    best_profit: Rational
    distribution: dict[Rational, Rational]

    @property
    def covered_probability(self) -> Rational:
        return Rational(self.covered_count, 37)

    @property
    def profitable_probability(self) -> Rational:
        return Rational(self.profitable_count, 37)

    @property
    def break_even_probability(self) -> Rational:
        return Rational(self.break_even_count, 37)

    @property
    def loss_probability(self) -> Rational:
        return Rational(self.loss_count, 37)


def _stake(value: object) -> Rational:
    """Interpret floats by their decimal spelling, avoiding binary artefacts."""
    if isinstance(value, bool):
        raise ValueError("stakes must be finite positive rational numbers")
    try:
        result = Rational(str(value))
    except (ValueError, TypeError, ZeroDivisionError) as exc:
        raise ValueError("stakes must be finite positive rational numbers") from exc
    if result.is_finite is not True or result <= 0:
        raise ValueError("stakes must be finite positive rational numbers")
    return result


def analyse(bets: Iterable[Bet], stakes: Iterable[object] | None = None) -> CoverageAnalysis:
    """Enumerate all 37 equally likely outcomes with exact positive stakes.

    Defaults to one unit per bet. Components share the same outcome; returned
    stake is included in gross receipts before subtracting the entire outlay.
    Synthetic standard-payout sets are accepted, as in ``Bet``; restrict inputs
    to ``european_catalogue`` when physical layout legality is required.
    """
    bets = tuple(bets)
    if not bets:
        raise ValueError("at least one bet is required")
    for bet in bets:
        validate_bet(Wheel.EUROPEAN, bet)
    amounts = tuple(_stake(value) for value in stakes) if stakes is not None else (Rational(1),) * len(bets)
    if len(amounts) != len(bets):
        raise ValueError("stakes must have one entry per bet")
    total = sum(amounts, Rational(0))
    profits = tuple(sum((amount * (bet.payout + 1)
                         for bet, amount in zip(bets, amounts) if pocket in bet.numbers),
                        Rational(0)) - total for pocket in range(37))
    counts = Counter(profits)
    expectation = sum(profits, Rational(0)) / 37
    return CoverageAnalysis(
        total_stake=total, profits=profits,
        covered_count=len(set().union(*(bet.numbers for bet in bets))),
        profitable_count=sum(1 for value in profits if value > 0),
        break_even_count=sum(value == 0 for value in profits),
        loss_count=sum(1 for value in profits if value < 0),
        expected_profit=expectation, return_per_unit_staked=expectation / total,
        worst_profit=min(profits), best_profit=max(profits),
        distribution={value: Rational(counts[value], 37) for value in sorted(counts)},
    )
