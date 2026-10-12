"""Bounded exhaustive equal-chip portfolio search on a fair European wheel."""
from __future__ import annotations

from itertools import combinations, islice
from math import comb
from typing import Sequence

import numpy as np

from roulette.rules import Bet, Wheel, validate_bet

THRESHOLDS = (70, 75, 80)


class SearchLimitExceeded(ValueError):
    """The declared search exceeds its explicit combination budget."""

    def __init__(self, combinations_required: int, max_combinations: int):
        self.combinations_required = combinations_required
        self.max_combinations = max_combinations
        super().__init__(f"Search requires {combinations_required} combinations; "
                         f"limit is {max_combinations}. No combinations searched.")


def combination_count(number_of_bets: int, max_bets: int) -> int:
    """Count all nonempty distinct subsets up to the requested size."""
    if type(number_of_bets) is not int or number_of_bets < 0:
        raise ValueError("number_of_bets must be a nonnegative integer")
    if type(max_bets) is not int or max_bets < 1:
        raise ValueError("max_bets must be a positive integer")
    return sum(comb(number_of_bets, k) for k in range(1, min(number_of_bets, max_bets) + 1))


def _representative(bets: Sequence[Bet], indices: Sequence[int], profits: np.ndarray) -> dict:
    covered = set().union(*(set(bets[i].numbers) for i in indices))
    values, counts = np.unique(profits, return_counts=True)
    positive, ties, losses = (int(np.count_nonzero(profits > 0)),
                              int(np.count_nonzero(profits == 0)),
                              int(np.count_nonzero(profits < 0)))
    k = len(indices)
    return {"bets": [bets[i].name for i in indices], "stake_per_bet": 1,
            "total_stake": k, "covered_count": len(covered),
            "profitable_count": positive, "break_even_count": ties, "loss_count": losses,
            "profitable_probability": f"{positive}/37", "covered_probability": f"{len(covered)}/37",
            "break_even_probability": f"{ties}/37", "loss_probability": f"{losses}/37",
            "expected_profit": f"-{k}/37", "return_per_unit_staked": "-1/37",
            "worst_profit": int(profits.min()), "best_profit": int(profits.max()),
            "profits_by_pocket": profits.tolist(),
            "distribution": [{"net_profit": int(v), "pocket_count": int(n),
                              "probability": f"{int(n)}/37"} for v, n in zip(values, counts)]}


def search_coverage(bets: Sequence[Bet], max_bets: int = 10,
                    max_combinations: int = 1_000_000, batch_size: int = 4096) -> dict:
    """Exhaust every allowed subset; maximise strictly positive net-profit outcomes.

    Each selected bet receives exactly one chip. Catalogue ordering breaks ties.
    This does not search repeated bets, unequal stakes or all possible allocations.
    """
    bets = tuple(bets)
    required = combination_count(len(bets), max_bets)
    for value, name in ((max_combinations, "max_combinations"), (batch_size, "batch_size")):
        if type(value) is not int or value < 1:
            raise ValueError(f"{name} must be a positive integer")
    if not bets:
        raise ValueError("at least one bet is required")
    if len({bet.name for bet in bets}) != len(bets):
        raise ValueError("bet names must be distinct")
    if len({(frozenset(bet.numbers), bet.payout) for bet in bets}) != len(bets):
        raise ValueError("catalogue contains duplicate bets")
    for bet in bets:
        validate_bet(Wheel.EUROPEAN, bet)
        if (bet.payout + 1) * len(bet.numbers) != 36:
            raise ValueError("requires standard European payouts")
    if required > max_combinations:
        raise SearchLimitExceeded(required, max_combinations)
    gross = np.zeros((len(bets), 37), dtype=np.int64)
    for i, bet in enumerate(bets):
        gross[i, list(bet.numbers)] = bet.payout + 1
    rows = []
    for k in range(1, min(max_bets, len(bets)) + 1):
        iterator = combinations(range(len(bets)), k)
        best_count, representative, examined = -1, None, 0
        qualifying = {t: 0 for t in THRESHOLDS}
        while batch := list(islice(iterator, batch_size)):
            indices = np.asarray(batch, dtype=np.int64)
            profits = gross[indices].sum(axis=1) - k
            positive = np.count_nonzero(profits > 0, axis=1)
            examined += len(batch)
            for threshold in THRESHOLDS:
                qualifying[threshold] += int(np.count_nonzero(100 * positive >= 37 * threshold))
            winner = int(np.argmax(positive))
            if int(positive[winner]) > best_count:
                best_count = int(positive[winner])
                representative = _representative(bets, batch[winner], profits[winner])
        rows.append({"number_of_bets": k, "combinations_searched": examined,
                     "maximum_profitable_count": best_count,
                     "maximum_profitable_probability": f"{best_count}/37",
                     "representative": representative,
                     "thresholds": {str(t): {"required_profitable_count": (37 * t + 99) // 100,
                                              "qualifying_combinations": qualifying[t],
                                              "representative": representative if qualifying[t] else None}
                                    for t in THRESHOLDS}})
    return {"status": "exhaustively_searched", "wheel": "european", "pockets": 37,
            "catalogue_size": len(bets), "max_bets": max_bets,
            "max_combinations": max_combinations, "combinations_required": required,
            "combinations_searched": sum(r["combinations_searched"] for r in rows),
            "scope": "Distinct selected catalogue bets, exactly one chip each; no unequal stakes or repeated bets.",
            "metric": "Strictly positive net profit after subtracting all stakes",
            "method": "Exhaustive integer settlement on all 37 equally likely pockets; no Monte Carlo uncertainty",
            "rng": None, "results": rows}
