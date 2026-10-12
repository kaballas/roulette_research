"""Bounded integer-chip optimisation with exact incumbent settlement checks.

HiGHS supplies a numerical MILP bound, not a formal exact-arithmetic proof of
optimality or infeasibility. Every returned allocation is independently settled
with rational arithmetic. The objective minimises the worst possible loss;
positive-profit pocket counts are constraints, not an expected-profit edge.
"""

from dataclasses import dataclass
from math import ceil, isfinite
from time import perf_counter
from typing import Iterable

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from roulette.coverage import CoverageAnalysis, analyse, european_catalogue
from roulette.rules import Bet


@dataclass(frozen=True)
class OptimisationResult:
    """Solver status and an exact-checked allocation, if an incumbent exists.

    Objective and dual bound have the minimisation sign: minus minimum profit.
    ``optimal`` identifies either a reconciled numerical integer bound or an
    attained analytical bound, distinguished by ``optimality_evidence``. Even
    a timed-out solver can supply an exactly settled allocation attaining the
    analytical bound. ``limit`` never asserts optimality.
    """

    status: str
    budget: int
    target_profitable: int
    max_bets: int
    bets: tuple[Bet, ...]
    stakes: tuple[int, ...]
    analysis: CoverageAnalysis | None
    solver_message: str
    solver_dual_bound: float | None
    solver_gap: float | None
    solver_objective: float | None
    analytical_upper_bound: int | None = None
    optimality_evidence: str = "none"
    elapsed_seconds: float = 0.0


def _integer(value: int, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer from {minimum} to {maximum}")
    return value


def optimise_coverage(
    budget: int = 37,
    target_profitable: int = 30,
    max_bets: int = 10,
    time_limit: float = 30.0,
    catalogue: Iterable[Bet] | None = None,
) -> OptimisationResult:
    """Maximise worst-pocket profit at a required positive-pocket count.

    Stakes are positive integer chips on at most ten distinct physical bets,
    summing exactly to ``budget``. A profitable pocket must return at least one
    net chip. The default catalogue is all 157 standard European layout bets.
    Smaller physical subsets support bounded experiments and exhaustive checks.
    No table-limit, denomination, French-rule or wheel-bias model is implied.
    """
    started = perf_counter()
    budget = _integer(budget, "budget", 1, 1_000_000)
    target_profitable = _integer(target_profitable, "target_profitable", 0, 37)
    max_bets = _integer(max_bets, "max_bets", 1, 10)
    if isinstance(time_limit, bool) or not isinstance(time_limit, (int, float)) or not isfinite(time_limit) or not 0 < time_limit <= 3600:
        raise ValueError("time_limit must be finite, positive and at most 3600 seconds")
    legal = tuple(bet for group in european_catalogue().values() for bet in group)
    candidates = tuple(catalogue) if catalogue is not None else legal
    legal_keys = {(frozenset(bet.numbers), bet.payout) for bet in legal}
    keys = []
    for bet in candidates:
        if not isinstance(bet, Bet) or (frozenset(bet.numbers), bet.payout) not in legal_keys:
            raise ValueError("catalogue must contain physical European layout bets")
        keys.append((frozenset(bet.numbers), bet.payout))
    if not candidates or len(set(keys)) != len(keys):
        raise ValueError("catalogue must be nonempty with distinct bets")
    # Every standard component has summed pocket profit -stake, hence sum p=-B.
    # At least r positive integer profits imply -B >= r + (37-r)*min(p).
    if target_profitable == 37:
        return OptimisationResult(
            "infeasible", budget, target_profitable, max_bets, (), (), None,
            "All 37 positive profits contradict exact summed profit -budget.",
            None, None, None, None, "analytical_infeasibility", perf_counter() - started)
    analytical_bound = (-budget - target_profitable) // (37 - target_profitable)
    if analytical_bound < -budget:
        return OptimisationResult(
            "infeasible", budget, target_profitable, max_bets, (), (), None,
            "Required profit count contradicts the analytical floor bound and maximum loss budget.",
            None, None, None, analytical_bound, "analytical_infeasibility", perf_counter() - started)

    n = len(candidates)
    # Variables: integer stakes x, binary active y, binary profitable z, floor t.
    size, z_start, t_index = 2 * n + 38, 2 * n, 2 * n + 37
    gross = np.array([[(bet.payout + 1) if pocket in bet.numbers else 0
                       for bet in candidates] for pocket in range(37)], dtype=float)
    rows, lower, upper = [], [], []

    def constraint(row: np.ndarray, low: float = -np.inf, high: float = np.inf) -> None:
        rows.append(row)
        lower.append(low)
        upper.append(high)

    for index in range(n):
        row = np.zeros(size)
        row[index], row[n + index] = 1, -budget
        constraint(row, high=0)  # x <= B*y
        row = np.zeros(size)
        row[index], row[n + index] = 1, -1
        constraint(row, low=0)  # x >= y
    row = np.zeros(size)
    row[:n] = 1
    constraint(row, low=budget, high=budget)
    row = np.zeros(size)
    row[n:2 * n] = 1
    constraint(row, high=max_bets)
    for pocket in range(37):
        row = np.zeros(size)
        row[:n], row[z_start + pocket] = gross[pocket], -(budget + 1)
        constraint(row, low=0)  # p >= 1 - (B+1)*(1-z), p = gross*x-B
        row = np.zeros(size)
        row[:n], row[t_index] = -gross[pocket], 1
        constraint(row, high=-budget)  # t <= p
    row = np.zeros(size)
    row[z_start:t_index] = 1
    constraint(row, low=target_profitable)
    objective = np.zeros(size)
    objective[t_index] = -1
    bounds = Bounds(np.r_[np.zeros(size - 1), -budget],
                    np.r_[np.full(n, budget), np.ones(n + 37), analytical_bound])
    result = milp(objective, integrality=np.ones(size), bounds=bounds,
                  constraints=LinearConstraint(np.array(rows), lower, upper),
                  options={"time_limit": float(time_limit), "mip_rel_gap": 0.0})
    if result.status not in (0, 1, 2):
        raise RuntimeError(f"coverage optimiser failed: {result.message}")

    def finite_field(name: str) -> float | None:
        value = getattr(result, name, None)
        return float(value) if value is not None and np.isfinite(value) else None

    dual, gap, fun = (finite_field(name) for name in ("mip_dual_bound", "mip_gap", "fun"))
    selected, stakes, analysis = (), (), None
    status = "infeasible" if result.status == 2 else "limit"
    evidence = "numerical_infeasibility" if result.status == 2 else "none"
    if result.x is not None and result.status != 2:
        raw = np.asarray(result.x)
        if raw.shape != (size,) or not np.all(np.isfinite(raw)) or not np.allclose(raw, np.rint(raw), rtol=0, atol=1e-6):
            raise RuntimeError("solver incumbent is not an integer allocation")
        integers = np.rint(raw).astype(np.int64)
        allocation = integers[:n]
        if np.any(allocation < 0) or np.sum(allocation) != budget or np.count_nonzero(allocation) > max_bets:
            raise RuntimeError("solver incumbent violates the allocation constraints")
        selected = tuple(bet for bet, amount in zip(candidates, allocation) if amount)
        stakes = tuple(int(amount) for amount in allocation if amount)
        analysis = analyse(selected, stakes)
        if analysis.profitable_count < target_profitable or integers[t_index] > analysis.worst_profit:
            raise RuntimeError("solver incumbent fails exact pocket validation")
        exact_objective = -int(analysis.worst_profit)
        if analysis.worst_profit == analytical_bound:
            status, evidence = "optimal", "analytical_bound_attained"
        elif (result.status == 0 and result.success and dual is not None
                and gap is not None and 0 <= gap <= 1e-7 and fun is not None
                and abs(fun - exact_objective) <= 1e-6
                and ceil(dual - 1e-7) == exact_objective):
            status = "optimal"
            evidence = "numerical_integer_bound"
    return OptimisationResult(status, budget, target_profitable, max_bets,
                              selected, stakes, analysis, str(result.message), dual, gap, fun,
                              analytical_bound, evidence, perf_counter() - started)
