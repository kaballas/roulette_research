"""Bounded integer-chip optimisation with exact incumbent settlement checks.

HiGHS supplies a numerical MILP bound, not a formal exact-arithmetic proof of
optimality or infeasibility. Every returned allocation is independently settled
with rational arithmetic. The objective minimises the worst possible loss;
positive-profit pocket counts are constraints, not an expected-profit edge.
"""

from dataclasses import dataclass
from math import ceil, gcd, isfinite
from functools import lru_cache, reduce
from itertools import product
from time import perf_counter
from typing import Iterable

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from roulette.coverage import CoverageAnalysis, analyse, european_catalogue
from roulette.rules import Bet


@dataclass(frozen=True)
class LatticeCertificate:
    """Necessary gross-return mass conditions; never a sufficiency claim.

    At floor t each receipt is rounded up to its pocket's payout gcd. To make
    r pockets profitable requires the r cheapest additional receipt increments.
    Their sum cannot exceed the exact total gross return 36*budget.
    """

    gross_gcds: tuple[int, ...]
    profitable_gross_thresholds: tuple[int | None, ...]
    total_gross: int
    minimum_required_gross: int | None
    upper_bound: int | None
    infeasible: bool
    mod3_bound_applied: bool = False
    mod3_minimum_nonzero_support: int | None = None


@lru_cache(maxsize=1)
def _mod3_minimum_nonzero_support() -> int:
    """Exact enumeration of six even-money stake residues, independent of stakes.

    Every other standard bet has gross payout divisible by three. All possible
    nonzero residue patterns therefore arise from these 3**6 assignments.
    """
    bets = european_catalogue()["even_money"]
    minimum = 37
    for residues in product(range(3), repeat=6):
        support = sum(sum(2 * amount for amount, bet in zip(residues, bets)
                          if pocket in bet.numbers) % 3 != 0 for pocket in range(37))
        if support:
            minimum = min(minimum, support)
    return minimum


def _lattice_certificate(gross, budget: int, target: int) -> LatticeCertificate:
    gcds = tuple(reduce(gcd, map(int, row), 0) for row in gross)
    thresholds = tuple(g * (budget // g + 1) if g else None for g in gcds)

    def mass(floor: int) -> int | None:
        receipt_floor = max(0, budget + floor)
        if receipt_floor and 0 in gcds:
            return None
        baseline = [((receipt_floor + g - 1) // g) * g if g else 0 for g in gcds]
        additional = sorted(max(0, threshold - base)
                            for threshold, base in zip(thresholds, baseline)
                            if threshold is not None)
        if len(additional) < target:
            return None
        return sum(baseline) + sum(additional[:target])

    minimum = mass(-budget)
    total = 36 * budget
    if minimum is None or minimum > total or target == 37:
        return LatticeCertificate(gcds, thresholds, total, minimum, None, True)
    low, high = -budget, (-budget - target) // (37 - target)
    if high < low:
        return LatticeCertificate(gcds, thresholds, total, minimum, high, True)
    while low < high:
        middle = (low + high + 1) // 2
        required = mass(middle)
        if required is not None and required <= total:
            low = middle
        else:
            high = middle - 1
    if budget == 20 and target == 34:
        residue_support = _mod3_minimum_nonzero_support()
        # 34 positive receipts consume >=714 of 720 total. At most six positive
        # pockets can have nonzero mod3 residue, plus at most three losers: <=9.
        # The enumerated minimum is16, hence all receipts are multiples of3.
        # A floor>-20 would then require >=34*21+3*3=723 gross, impossible.
        if residue_support > 9:
            return LatticeCertificate(gcds, thresholds, total, minimum,
                                      min(low, -20), False, True, residue_support)
    return LatticeCertificate(gcds, thresholds, total, minimum, low, False)


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
    mode: str = "optimise"
    backend: str = "highs"
    incumbent_used: bool = False
    lattice_certificate: LatticeCertificate | None = None


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
    *,
    mode: str = "optimise",
    backend: str = "highs",
    incumbent: OptimisationResult | tuple[Iterable[Bet], Iterable[int]] | None = None,
) -> OptimisationResult:
    """Maximise worst-pocket profit at a required positive-pocket count.

    Stakes are positive integer chips on at most ten distinct physical bets,
    summing exactly to ``budget``. A profitable pocket must return at least one
    net chip. The default catalogue is all 157 standard European layout bets.
    Smaller physical subsets support bounded experiments and exhaustive checks.
    No table-limit, denomination, French-rule or wheel-bias model is implied.
    ``feasibility`` mode stops at a verified feasible allocation and makes no
    optimality claim. A supplied incumbent is exactly checked before use as a
    floor constraint; HiGHS has no incumbent warm-start interface. CP-SAT also
    receives it as a hint. No unproved layout symmetries are imposed.
    """
    started = perf_counter()
    budget = _integer(budget, "budget", 1, 1_000_000)
    target_profitable = _integer(target_profitable, "target_profitable", 0, 37)
    max_bets = _integer(max_bets, "max_bets", 1, 10)
    if mode not in ("optimise", "feasibility"):
        raise ValueError("mode must be 'optimise' or 'feasibility'")
    if backend not in ("highs", "cpsat"):
        raise ValueError("backend must be 'highs' or 'cpsat'")
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
    n = len(candidates)
    gross = np.array([[(bet.payout + 1) if pocket in bet.numbers else 0
                       for bet in candidates] for pocket in range(37)], dtype=np.int64)
    lattice = _lattice_certificate(gross, budget, target_profitable)
    selected, stakes, analysis, initial_allocation = (), (), None, None
    if incumbent is not None:
        if isinstance(incumbent, OptimisationResult):
            initial_bets, initial_stakes = incumbent.bets, incumbent.stakes
        else:
            try:
                initial_bets, initial_stakes = incumbent
            except (TypeError, ValueError) as exc:
                raise ValueError("incumbent must contain bets and integer stakes") from exc
        initial_bets, initial_stakes = tuple(initial_bets), tuple(initial_stakes)
        if not initial_bets or len(initial_bets) != len(initial_stakes):
            raise ValueError("incumbent must contain matching nonempty bets and stakes")
        initial_allocation = np.zeros(n, dtype=np.int64)
        for bet, amount in zip(initial_bets, initial_stakes):
            amount = _integer(amount, "incumbent stake", 1, budget)
            if not isinstance(bet, Bet) or (frozenset(bet.numbers), bet.payout) not in keys:
                raise ValueError("incumbent bet is outside the selected catalogue")
            index = keys.index((frozenset(bet.numbers), bet.payout))
            if initial_allocation[index]:
                raise ValueError("incumbent bets must be distinct")
            initial_allocation[index] = amount
        if sum(initial_stakes) != budget or len(initial_bets) > max_bets:
            raise ValueError("incumbent violates budget or active bet limit")
        selected, stakes = initial_bets, initial_stakes
        analysis = analyse(selected, stakes)
        if analysis.profitable_count < target_profitable:
            raise ValueError("incumbent does not meet the requested profitable-pocket target")

    def answer(status, message, evidence, bound, dual=None, gap=None, fun=None):
        return OptimisationResult(
            status, budget, target_profitable, max_bets, selected, stakes, analysis,
            message, dual, gap, fun, bound, evidence, perf_counter() - started,
            mode, backend, incumbent is not None, lattice)

    if lattice.infeasible:
        if analysis is not None:
            raise RuntimeError("verified incumbent contradicts analytical lattice bound")
        scalar_bound = None if target_profitable == 37 else (-budget - target_profitable) // (37 - target_profitable)
        return answer("infeasible", "Exact gross-return lattice mass rules out this target.",
                      "analytical_infeasibility", scalar_bound)
    analytical_bound = lattice.upper_bound
    if analysis is not None and mode == "feasibility":
        return answer("feasible", "Supplied allocation passed exact feasibility checks.",
                      "exact_feasible_allocation", analytical_bound)
    if analysis is not None and analysis.worst_profit == analytical_bound:
        return answer("optimal", "Supplied allocation attains exact lattice upper bound.",
                      "analytical_bound_attained", analytical_bound)
    floor_lower = int(analysis.worst_profit) if analysis is not None else -budget
    # Variables: integer stakes x, binary active y, binary profitable z, floor t.
    size, z_start, t_index = 2 * n + 38, 2 * n, 2 * n + 37
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
        threshold = lattice.profitable_gross_thresholds[pocket]
        row[:n], row[z_start + pocket] = gross[pocket], -(threshold or 1)
        constraint(row, low=0)  # lattice-strengthened positive-profit implication
        row = np.zeros(size)
        row[:n], row[t_index] = -gross[pocket], 1
        constraint(row, high=-budget)  # t <= p
    row = np.zeros(size)
    row[z_start:t_index] = 1
    constraint(row, low=target_profitable)
    objective = np.zeros(size)
    objective[t_index] = -1 if mode == "optimise" else 0
    bounds = Bounds(np.r_[np.zeros(size - 1), floor_lower],
                    np.r_[np.full(n, budget), np.ones(n + 37), analytical_bound])
    if backend == "highs":
        result = milp(objective, integrality=np.ones(size), bounds=bounds,
                      constraints=LinearConstraint(np.array(rows), lower, upper),
                      options={"time_limit": float(time_limit), "mip_rel_gap": 0.0})
    else:
        from roulette.coverage_cpsat import solve_cpsat
        result = solve_cpsat(gross, budget, target_profitable, max_bets,
                             floor_lower, analytical_bound, lattice.profitable_gross_thresholds,
                             mode, time_limit, initial_allocation)
    if result.status not in (0, 1, 2):
        raise RuntimeError(f"coverage optimiser failed: {result.message}")

    def finite_field(name: str) -> float | None:
        value = getattr(result, name, None)
        return float(value) if value is not None and np.isfinite(value) else None

    dual, gap, fun = (finite_field(name) for name in ("mip_dual_bound", "mip_gap", "fun"))
    status = "infeasible" if result.status == 2 else "limit"
    evidence = (("cpsat_infeasibility" if backend == "cpsat" else "numerical_infeasibility")
                if result.status == 2 else "none")
    if result.status == 2 and analysis is not None:
        raise RuntimeError("solver infeasibility contradicts a verified supplied incumbent")
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
        if (analysis.profitable_count < target_profitable or integers[t_index] > analysis.worst_profit
                or analysis.worst_profit < floor_lower):
            raise RuntimeError("solver incumbent fails exact pocket validation")
        exact_objective = -int(analysis.worst_profit)
        if mode == "feasibility":
            status, evidence = "feasible", "exact_feasible_allocation"
        elif analysis.worst_profit == analytical_bound:
            status, evidence = "optimal", "analytical_bound_attained"
        elif (result.status == 0 and result.success and dual is not None
                and gap is not None and 0 <= gap <= 1e-7 and fun is not None
                and abs(fun - exact_objective) <= 1e-6
                and ceil(dual - 1e-7) == exact_objective):
            status = "optimal"
            evidence = "cpsat_integer_bound" if backend == "cpsat" else "numerical_integer_bound"
    if mode == "feasibility":
        dual, gap, fun = None, None, None
    return answer(status, str(result.message), evidence, analytical_bound, dual, gap, fun)
