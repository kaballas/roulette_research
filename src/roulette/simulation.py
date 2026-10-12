"""Seeded simulations using independent uniform draws from explicit pockets."""

from __future__ import annotations

from numbers import Integral
from typing import TYPE_CHECKING

import numpy as np

from roulette.rules import Bet, Wheel, french_even_money, pockets, validate_bet

if TYPE_CHECKING:
    from roulette.strategies import Portfolio


def _positive_integer(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def _draw_completed(
    wheel: Wheel, bet: Bet, n: int, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """Draw completed wagers and count every physical spin, including holds."""
    outcomes = rng.choice(pockets(wheel), size=n)
    profits = np.where(np.isin(outcomes, bet.numbers), float(bet.payout), -1.0)
    spins = np.ones(n, dtype=np.int64)
    even_money = french_even_money(bet)
    if even_money and wheel == Wheel.LA_PARTAGE:
        profits[outcomes == 0] = -0.5
    elif even_money and wheel == Wheel.EN_PRISON:
        pending = np.flatnonzero(outcomes == 0)
        while pending.size:
            resolving = rng.choice(pockets(wheel), size=pending.size)
            spins[pending] += 1
            finished = resolving != 0
            profits[pending[finished]] = np.where(
                np.isin(resolving[finished], bet.numbers), 0.0, -1.0
            )
            pending = pending[~finished]
    return profits, spins


def simulate_wagers(wheel: Wheel, bet: Bet, n: int, seed: int) -> np.ndarray:
    """Return net unit profits for ``n`` completed, independent wagers.

    A wager starts with one unit staked. En prison wagers can consume several
    spins, but resolving spins do not constitute additional stakes. A zero on
    an imprisoned even-money wager holds it; a subsequent win returns its stake
    (zero net profit) and a subsequent loss forfeits it. This is an explicit
    repeated-zero-holds convention, rather than a universal casino rule.
    """
    n = _positive_integer(n, "n")
    wheel = Wheel(wheel)
    validate_bet(wheel, bet)
    rng = np.random.default_rng(seed)
    return _draw_completed(wheel, bet, n, rng)[0]


def simulate_sessions(
    wheel: Wheel,
    bet: Bet | Portfolio,
    strategy: str,
    sessions: int,
    max_wagers: int,
    bankroll: float,
    table_min: float,
    table_max: float,
    seed: int,
    base: float = 1.0,
) -> dict[str, np.ndarray]:
    """Simulate bounded, independent sessions with no stake clipping.

    The wager horizon counts completed new stakes, not prison resolution spins.
    Every stake must be affordable and within the table limits before it is
    placed. Portfolio component stakes each satisfy the table minimum/maximum,
    and total stake also satisfies the maximum. Portfolios share one outcome
    per wager and currently support standard European/American rules only.

    Drawdown is peak-to-trough *settled* bankroll; it excludes temporary stake
    reservation, including time spent en prison. Ruin means settled funds reach
    zero. Insufficient positive funds and limit breaches are separate flags.
    """
    from roulette.strategies import Portfolio, make_strategy

    sessions = _positive_integer(sessions, "sessions")
    max_wagers = _positive_integer(max_wagers, "max_wagers")
    wheel = Wheel(wheel)
    for name, value in (("bankroll", bankroll), ("table_min", table_min),
                        ("table_max", table_max), ("base", base)):
        if isinstance(value, bool) or not np.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive")
    if table_min > table_max:
        raise ValueError("table_min must not exceed table_max")
    if isinstance(bet, Portfolio):
        if wheel not in (Wheel.EUROPEAN, Wheel.AMERICAN):
            raise ValueError("portfolios currently require standard wheel rules")
        for component, _weight in bet.components:
            validate_bet(wheel, component)
        weights = np.array([weight for _component, weight in bet.components])
    else:
        validate_bet(wheel, bet)
        weights = np.ones(1)

    policy = make_strategy(strategy, sessions, base)
    rng = np.random.default_rng(seed)
    funds = np.full(sessions, float(bankroll))
    peaks = funds.copy()
    turnover = np.zeros(sessions)
    wagers = np.zeros(sessions, dtype=np.int64)
    spins = np.zeros(sessions, dtype=np.int64)
    drawdown = np.zeros(sessions)
    active = np.ones(sessions, dtype=bool)
    ruined = np.zeros(sessions, dtype=bool)
    limit_stopped = np.zeros(sessions, dtype=bool)
    bankroll_stopped = np.zeros(sessions, dtype=bool)

    for _ in range(max_wagers):
        indices = np.flatnonzero(active)
        if not indices.size:
            break
        requested = np.asarray(policy.stakes(), dtype=float)[indices]
        allocations = requested[:, None] * weights
        invalid = (~np.isfinite(requested) | (requested <= 0)
                   | (requested > table_max)
                   | np.any(allocations < table_min, axis=1)
                   | np.any(allocations > table_max, axis=1))
        unaffordable = requested > funds[indices]
        limit_stopped[indices[invalid]] = True
        bankroll_stopped[indices[unaffordable]] = True
        active[indices[invalid | unaffordable]] = False
        eligible = ~(invalid | unaffordable)
        indices = indices[eligible]
        stakes = requested[eligible]
        if not indices.size:
            continue

        if isinstance(bet, Portfolio):
            outcomes = rng.choice(pockets(wheel), size=indices.size)
            # Sum returned stakes plus winnings, then debit the initial unit
            # once. This makes a complete portfolio loss exactly -1 even when
            # fractional component weights have floating-point roundoff.
            unit_profit = np.full(indices.size, -1.0)
            for component, weight in bet.components:
                unit_profit += weight * np.where(
                    np.isin(outcomes, component.numbers), component.payout + 1, 0.0
                )
            used_spins = np.ones(indices.size, dtype=np.int64)
        else:
            unit_profit, used_spins = _draw_completed(wheel, bet, indices.size, rng)
        funds[indices] += stakes * unit_profit
        turnover[indices] += stakes
        wagers[indices] += 1
        spins[indices] += used_spins
        peaks[indices] = np.maximum(peaks[indices], funds[indices])
        drawdown[indices] = np.maximum(drawdown[indices], peaks[indices] - funds[indices])
        policy.update(indices, unit_profit)
        depleted = funds[indices] <= 0
        ruined[indices[depleted]] = True
        active[indices[depleted]] = False

    return {"profit": funds - bankroll, "turnover": turnover, "wagers": wagers,
            "spins": spins, "max_drawdown": drawdown, "ruined": ruined,
            "limit_stopped": limit_stopped, "bankroll_stopped": bankroll_stopped}
