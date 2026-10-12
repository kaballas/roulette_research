"""Distinct integer-chip portfolios on a fair single-zero European wheel.

Each search solves a sequence of MILPs. After every solution a Hamming-distance
cut on the set of active bets forces the next portfolio to differ in at least
``min_distance`` positions, so alternatives are structurally different bet sets
and not restaking or one-bet tweaks of one portfolio. Every returned allocation
is re-settled with exact rational arithmetic. HiGHS bounds are numerical, so
"proven" flags are solver evidence, not formal proofs.

Whatever is returned, each portfolio has expectation exactly ``-stake/37``
(return ``-1/37`` per chip): ranking by coverage or tail risk never creates an
edge. Objectives are one-spin measures only.
"""

from dataclasses import dataclass
from fractions import Fraction
from math import isfinite
from time import perf_counter
from typing import Iterable

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from roulette.coverage import CoverageAnalysis, analyse, european_catalogue
from roulette.coverage_optimisation import _lattice_certificate
from roulette.coverage_risk import ExactRisk, exact_risk
from roulette.rules import Bet

OBJECTIVES = ("frequency", "worst_loss", "tail")
STAKE_MODES = ("any", "equal")
DEFAULT_FAMILIES = ("split", "corner", "street", "six_line", "dozen", "column", "even_money")


@dataclass(frozen=True)
class Portfolio:
    """One exactly settled alternative; ``objective_value`` is minimised."""

    rank: int
    bets: tuple[Bet, ...]
    stakes: tuple[int, ...]
    analysis: CoverageAnalysis
    risk: ExactRisk
    objective_value: Fraction
    solver_status: str
    proven_best_remaining: bool


@dataclass(frozen=True)
class Exploration:
    """Portfolios for one (budget, max_bets, target, objective, stakes) cell.

    ``stop_reason``: ``count_reached``; ``exhausted`` (solver reports no further
    portfolio at the distance, numerically); ``analytical_infeasible`` (exact
    lattice argument); ``time_limit`` (a solve ended without an incumbent, not
    proof that none exists); ``twin_limit`` (more candidates than tolerated
    repeated an accepted P&L distribution; neither exhaustion nor a time limit).
    For ``frequency`` the search instead descends: after that many twins the
    profitable-pocket count is capped below the saturated level and continues.
    """

    budget: int
    max_bets: int
    target_profitable: int
    objective: str
    stake_mode: str
    min_distance: int
    requested: int
    portfolios: tuple[Portfolio, ...]
    stop_reason: str
    elapsed_seconds: float
    realised_min_distance: int | None


def _key(bet: Bet) -> tuple[frozenset[int], int]:
    return frozenset(bet.numbers), bet.payout


def objective_value(analysis: CoverageAnalysis, risk: ExactRisk, objective: str) -> Fraction:
    """Exact minimisation-form objective: lower is better for every objective."""
    if objective == "worst_loss":
        return -Fraction(str(analysis.worst_profit))
    if objective == "tail":
        return risk.expected_shortfall
    width = 2 * int(analysis.total_stake) + 1
    return -Fraction(width * analysis.profitable_count) - Fraction(str(analysis.worst_profit))


def catalogue_for(families: Iterable[str]) -> tuple[Bet, ...]:
    groups = european_catalogue()
    names = list(dict.fromkeys(families))
    unknown = [name for name in names if name not in groups]
    if unknown:
        raise ValueError(f"unknown bet families: {unknown}")
    return tuple(bet for name in names for bet in groups[name])


def _integer(value: int, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer from {low} to {high}")
    return value


def _equal_sizes(budget: int, max_bets: int) -> list[int]:
    return [k for k in range(1, max_bets + 1) if budget % k == 0]


def _solve_once(candidates, gross, budget, target, max_bets, objective, stake_mode,
                alpha, cuts, min_distance, time_limit, upper_floor, count_cap=None):
    n = len(candidates)
    z0, t_i, eta_i, u0 = 2 * n, 2 * n + 37, 2 * n + 38, 2 * n + 39
    sizes = _equal_sizes(budget, max_bets) if stake_mode == "equal" else []
    s0 = u0 + 37
    size = s0 + len(sizes)
    rows, low, high = [], [], []

    def add(row, lo=-np.inf, hi=np.inf):
        rows.append(row)
        low.append(lo)
        high.append(hi)

    for i in range(n):
        row = np.zeros(size)
        row[i], row[n + i] = 1, -budget
        add(row, hi=0)
        row = np.zeros(size)
        row[i], row[n + i] = 1, -1
        add(row, lo=0)
    row = np.zeros(size)
    row[:n] = 1
    add(row, budget, budget)
    row = np.zeros(size)
    row[n:2 * n] = 1
    add(row, hi=max_bets)
    gcds = [int(np.gcd.reduce(gross[p])) for p in range(37)]
    for p in range(37):
        g = gcds[p]
        row = np.zeros(size)
        row[:n] = gross[p]
        row[z0 + p] = -(g * (budget // g + 1) if g else 1)
        add(row, lo=0)
    row = np.zeros(size)
    row[z0:z0 + 37] = 1
    add(row, lo=target)
    if objective == "frequency":
        # z_p = 0 forces profit <= 0, so sum(z) is exactly the profitable count
        for p in range(37):
            row = np.zeros(size)
            row[:n] = gross[p]
            row[z0 + p] = -(int(gross[p].max()) - 1) * budget
            add(row, hi=budget)
        if count_cap is not None:
            row = np.zeros(size)
            row[z0:z0 + 37] = 1
            add(row, hi=count_cap)
    if objective in ("worst_loss", "frequency"):
        for p in range(37):
            row = np.zeros(size)
            row[:n], row[t_i] = -gross[p], 1
            add(row, hi=-budget)
    if objective == "tail":
        for p in range(37):
            row = np.zeros(size)
            row[:n], row[eta_i], row[u0 + p] = gross[p], 1, 1
            add(row, lo=budget)  # u_p >= loss_p - eta
    if stake_mode == "equal":
        row = np.zeros(size)
        row[s0:] = 1
        add(row, 1, 1)
        row = np.zeros(size)
        row[n:2 * n] = 1
        row[s0:] = [-k for k in sizes]
        add(row, 0, 0)  # active count equals the selected size
        for j, k in enumerate(sizes):
            chips = budget // k
            for i in range(n):
                row = np.zeros(size)
                row[i], row[n + i], row[s0 + j] = 1, -chips, budget
                add(row, hi=budget)  # x_i <= chips*y_i when size k selected
                row = np.zeros(size)
                row[i], row[n + i], row[s0 + j] = 1, -chips, -budget
                add(row, lo=-budget)  # x_i >= chips*y_i when size k selected
    for chosen in cuts:
        row = np.full(size, 0.0)
        row[n:2 * n] = [-1.0] * n
        for i in chosen:
            row[n + i] = 1.0
        add(row, hi=len(chosen) - min_distance)  # Hamming distance >= min_distance
    cost = np.zeros(size)
    if objective == "worst_loss":
        cost[t_i] = -1
    elif objective == "frequency":
        cost[z0:z0 + 37] = -(2 * budget + 1)
        cost[t_i] = -1
    else:
        cost[eta_i] = alpha  # alpha * ES, avoiding a huge reciprocal for small alpha
        cost[u0:u0 + 37] = 1 / 37
    lower, upper = np.zeros(size), np.zeros(size)
    upper[:n] = budget
    upper[n:z0 + 37] = 1
    if objective in ("worst_loss", "frequency"):
        lower[t_i], upper[t_i] = -budget, upper_floor
    if objective == "tail":
        lower[eta_i], upper[eta_i] = -36 * budget, budget
        upper[u0:u0 + 37] = 37 * budget
    upper[s0:] = 1
    integrality = np.ones(size)
    integrality[[t_i, eta_i]] = 0
    integrality[u0:u0 + 37] = 0
    result = milp(cost, integrality=integrality, bounds=Bounds(lower, upper),
                  constraints=LinearConstraint(np.array(rows), low, high),
                  options={"time_limit": float(time_limit), "mip_rel_gap": 0.0})
    return result, n


def explore_portfolios(
    budget: int = 20,
    target_profitable: int = 26,
    max_bets: int = 10,
    objective: str = "worst_loss",
    catalogue: Iterable[Bet] | None = None,
    *,
    count: int = 10,
    min_distance: int = 4,
    stake_mode: str = "any",
    time_limit: float = 30.0,
    alpha: Fraction = Fraction(1, 20),
    exclude: Iterable[Iterable[Bet]] = (),
) -> Exploration:
    """Return up to ``count`` best-found portfolios, pairwise ``min_distance`` apart.

    ``exclude`` bet sets (for example a reference portfolio) are also kept at
    that distance. Portfolios sharing the sorted 37-pocket P&L multiset of an
    accepted one (mirror/shifted twins) are discarded, so alternatives differ in
    risk profile and not only in table position. A reference's profile is not
    pre-seeded; the CLI compares it separately. Every pocket-profit target is a minimum count of pockets
    with strictly positive net profit.
    """
    started = perf_counter()
    budget = _integer(budget, "budget", 1, 1_000_000)
    target_profitable = _integer(target_profitable, "target_profitable", 0, 37)
    max_bets = _integer(max_bets, "max_bets", 1, 10)
    count = _integer(count, "count", 1, 50)
    min_distance = _integer(min_distance, "min_distance", 1, 20)
    if objective not in OBJECTIVES:
        raise ValueError(f"objective must be one of {OBJECTIVES}")
    if stake_mode not in STAKE_MODES:
        raise ValueError(f"stake_mode must be one of {STAKE_MODES}")
    if isinstance(time_limit, bool) or not isinstance(time_limit, (int, float)) \
            or not isfinite(time_limit) or not 0 < time_limit <= 3600:
        raise ValueError("time_limit must be finite, positive and at most 3600 seconds")
    alpha = Fraction(alpha)
    if not Fraction(1, 10**6) <= alpha <= 1:
        raise ValueError("alpha must be in [1e-6, 1]")
    legal = {_key(b) for group in european_catalogue().values() for b in group}
    candidates = tuple(catalogue) if catalogue is not None else catalogue_for(DEFAULT_FAMILIES)
    keys = [_key(b) for b in candidates]
    if not candidates or len(set(keys)) != len(keys) or not set(keys) <= legal:
        raise ValueError("catalogue must be distinct physical European layout bets")
    index = {k: i for i, k in enumerate(keys)}
    gross = np.array([[(b.payout + 1) if p in b.numbers else 0 for b in candidates]
                      for p in range(37)], dtype=np.int64)
    cuts: list[tuple[int, ...]] = []
    for bets in exclude:
        chosen = tuple(sorted(index[_key(b)] for b in bets if _key(b) in index))
        if chosen:
            cuts.append(chosen)

    def finish(portfolios, reason):
        portfolios = [Portfolio(i + 1, p.bets, p.stakes, p.analysis, p.risk,
                                p.objective_value, p.solver_status, p.proven_best_remaining)
                      for i, p in enumerate(sorted(portfolios,
                                                   key=lambda q: (q.objective_value, q.rank)))]
        sets = [frozenset(index[_key(b)] for b in p.bets) for p in portfolios]
        gaps = [len(a ^ b) for i, a in enumerate(sets) for b in sets[i + 1:]]
        return Exploration(budget, max_bets, target_profitable, objective, stake_mode,
                           min_distance, count, tuple(portfolios), reason,
                           perf_counter() - started, min(gaps) if gaps else None)

    lattice = _lattice_certificate(gross, budget, target_profitable)
    if lattice.infeasible:
        return finish([], "analytical_infeasible")
    if stake_mode == "equal" and not _equal_sizes(budget, max_bets):
        return finish([], "analytical_infeasible")
    found: list[Portfolio] = []
    seen_profiles: set[tuple] = set()
    rejected, max_twins, count_cap = 0, count, None
    while len(found) < count:
        result, n = _solve_once(candidates, gross, budget, target_profitable, max_bets,
                                objective, stake_mode, float(alpha), cuts, min_distance,
                                time_limit, lattice.upper_bound, count_cap)
        if result.status == 2:
            return finish(found, "exhausted")
        if result.x is None:
            return finish(found, "time_limit")
        if result.status not in (0, 1):
            raise RuntimeError(f"explorer solve failed: {result.message}")
        raw = np.asarray(result.x)
        if not np.allclose(raw[:2 * n + 37], np.rint(raw[:2 * n + 37]), rtol=0, atol=1e-6):
            raise RuntimeError("solver incumbent is not an integer allocation")
        amounts = np.rint(raw[:n]).astype(np.int64)
        if np.any(amounts < 0) or amounts.sum() != budget or np.count_nonzero(amounts) > max_bets:
            raise RuntimeError("solver incumbent violates allocation constraints")
        chosen = tuple(int(i) for i in np.flatnonzero(amounts))
        bets = tuple(candidates[i] for i in chosen)
        stakes = tuple(int(amounts[i]) for i in chosen)
        if stake_mode == "equal" and len(set(stakes)) != 1:
            raise RuntimeError("equal-stake mode returned unequal stakes")
        analysis = analyse(bets, stakes)
        if analysis.profitable_count < target_profitable:
            raise RuntimeError("solver incumbent fails exact profitable-pocket target")
        if analysis.expected_profit != -analysis.total_stake / 37:
            raise RuntimeError("exact European expectation identity violated")
        chosen_set = frozenset(chosen)
        for previous in cuts:
            if len(chosen_set ^ frozenset(previous)) < min_distance:
                raise RuntimeError("solver incumbent violates the distance cut")
        cuts.append(chosen)
        profile = tuple(sorted(analysis.profits))
        if profile in seen_profiles:
            rejected += 1  # mirror or shifted twin: same risk profile, new positions
            if rejected > max_twins:
                if objective != "frequency":
                    return finish(found, "twin_limit")
                # level descent: this profitable-pocket level is saturated by twins
                count_cap = analysis.profitable_count - 1
                rejected = 0
                if count_cap < target_profitable:
                    return finish(found, "exhausted")
            continue
        seen_profiles.add(profile)
        risk = exact_risk(analysis, alpha)
        value = objective_value(analysis, risk, objective)
        proven = result.status == 0 and bool(result.success)
        found.append(Portfolio(len(found) + 1, bets, stakes, analysis, risk, value,
                               "optimal" if proven else "limit", proven))
    return finish(found, "count_reached")


def describe_bet(bet: Bet) -> str:
    """Table-position label such as ``Split 7/8`` or ``Six-line 4-9``."""
    numbers = sorted(bet.numbers)
    family = bet.name.split("_")[0]
    if bet.name in ("red", "black", "odd", "even", "low", "high"):
        return {"low": "Low 1-18", "high": "High 19-36"}.get(bet.name, bet.name.capitalize())
    if family == "six":
        return f"Six-line {numbers[0]}-{numbers[-1]}"
    if family == "dozen":
        return f"Dozen {numbers[0]}-{numbers[-1]}"
    if family == "column":
        return f"Column {numbers[0]}-{numbers[-1]} (1st/2nd/3rd = starts 1/2/3)"
    return f"{family.capitalize()} " + "/".join(map(str, numbers))
