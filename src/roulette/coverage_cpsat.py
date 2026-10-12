"""Optional CP-SAT adapter; no OR-Tools import until explicitly requested."""

from types import SimpleNamespace


def solve_cpsat(gross, budget, target, max_bets, floor_lower, floor_upper,
                thresholds, mode, time_limit, incumbent=None):
    """Return a SciPy-like result for shared exact incumbent validation.

    CP-SAT uses integer constraints. Its solver certificate is not a checked
    external proof. One worker and a fixed seed make configuration reproducible;
    wall-clock limits can still affect the incumbent returned.
    """
    try:
        from ortools.sat.python import cp_model
    except ImportError as exc:
        raise ImportError("The cpsat backend requires optional dependency 'ortools'.") from exc

    model = cp_model.CpModel()
    n = len(gross[0])
    stakes = [model.NewIntVar(0, budget, f"stake_{i}") for i in range(n)]
    active = [model.NewBoolVar(f"active_{i}") for i in range(n)]
    profitable = [model.NewBoolVar(f"profitable_{i}") for i in range(37)]
    floor = model.NewIntVar(floor_lower, floor_upper, "profit_floor")
    for x, y in zip(stakes, active):
        model.Add(x <= budget * y)
        model.Add(x >= y)
    model.Add(sum(stakes) == budget)
    model.Add(sum(active) <= max_bets)
    for pocket, row in enumerate(gross):
        receipt = sum(int(coefficient) * x for coefficient, x in zip(row, stakes))
        model.Add(floor <= receipt - budget)
        threshold = thresholds[pocket]
        if threshold is None:
            model.Add(profitable[pocket] == 0)
        else:
            model.Add(receipt >= threshold).OnlyEnforceIf(profitable[pocket])
            model.Add(receipt <= threshold - 1).OnlyEnforceIf(profitable[pocket].Not())
    model.Add(sum(profitable) >= target)
    if mode == "optimise":
        model.Minimize(-floor)
    if incumbent is not None:
        for variable, amount in zip(stakes, incumbent):
            model.AddHint(variable, int(amount))
        for variable, amount in zip(active, incumbent):
            model.AddHint(variable, int(amount > 0))
        receipts = [sum(int(c) * int(x) for c, x in zip(row, incumbent)) for row in gross]
        for variable, receipt in zip(profitable, receipts):
            model.AddHint(variable, int(receipt > budget))
        model.AddHint(floor, min(receipts) - budget)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit)
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    code = solver.Solve(model)
    if code == cp_model.MODEL_INVALID:
        raise RuntimeError(f"CP-SAT rejected coverage model: {solver.ResponseStats()}")
    status = 2 if code == cp_model.INFEASIBLE else (0 if code == cp_model.OPTIMAL else 1)
    values = None
    objective = dual = gap = None
    if code in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        values = [solver.Value(v) for v in stakes + active + profitable + [floor]]
        if mode == "optimise":
            objective = float(solver.ObjectiveValue())
            dual = float(solver.BestObjectiveBound())
            gap = abs(objective - dual) / max(1, abs(objective))
    return SimpleNamespace(status=status, success=status == 0,
                           message=f"CP-SAT {solver.StatusName(code)}; workers=1; seed=0",
                           x=values, fun=objective, mip_dual_bound=dual, mip_gap=gap)
