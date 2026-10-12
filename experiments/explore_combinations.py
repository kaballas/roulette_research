"""Roulette Combination Explorer: distinct integer-chip portfolios per search cell.

Searches chip budgets, position limits, target profitable-pocket percentages,
objectives and stake modes on a fair single-zero European wheel. Every cell
returns several pairwise-distinct portfolios with exact bets, chips and net
profit on all 37 pockets. Each portfolio has expectation exactly -stake/37.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
import argparse
from fractions import Fraction
import hashlib
from importlib.metadata import PackageNotFoundError, version
from itertools import product
import json
import math
from pathlib import Path
import subprocess

from baseline import ROOT, metadata
from benchmark_coverage import checked_seed
from optimise_coverage import _chip_budget, _json_exact, _percentage, _position_limit
from roulette.coverage import analyse, european_catalogue
from roulette.coverage_explorer import (
    DEFAULT_FAMILIES, OBJECTIVES, Exploration, catalogue_for, describe_bet,
    explore_portfolios, objective_value,
)
from roulette.coverage_risk import exact_risk
from roulette.rules import Bet

DEFAULT_REFERENCES = ("coverage-benchmark-060.json", "coverage-optimisation-20chips.json")
OBJECTIVE_TEXT = {
    "frequency": "highest winning frequency (then smallest worst loss)",
    "worst_loss": "lowest worst loss",
    "tail": "smallest losing tail (5% expected shortfall)",
}


def _count(value: str) -> int:
    number = int(value)
    if not 1 <= number <= 20:
        raise argparse.ArgumentTypeError("count must be between 1 and 20")
    return number


def _seconds(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or not 0 < number <= 3600:
        raise argparse.ArgumentTypeError("seconds must be finite, positive and at most 3600")
    return number


def load_references(paths, catalogue, budget, max_bets, required,
                    objective="worst_loss", stake_mode="any"):
    """Best exact-checked recorded portfolio for this cell's objective, or ``None``.

    Equal-stake cells accept only equal-chip references. Ranking uses the same
    exact objective as the explorer, so row A is comparable with its siblings.
    """
    best = None
    for path in paths:
        if not path.exists():
            continue
        for row in json.loads(path.read_bytes())["results"]:
            for part in (row, row.get("feasibility"), row.get("optimisation")):
                if not isinstance(part, dict) or not part.get("bets"):
                    continue
                bets = [Bet(b["name"], tuple(b["numbers"]), b["payout"]) for b in part["bets"]]
                seed = checked_seed(bets, part.get("stakes", []), str(path.name),
                                    catalogue, budget, max_bets)
                if seed is None or (stake_mode == "equal" and len(set(seed.stakes)) != 1):
                    continue
                analysis = analyse(seed.bets, seed.stakes)
                if analysis.profitable_count < required:
                    continue
                value = objective_value(analysis, exact_risk(analysis), objective)
                if best is None or value < best[0]:
                    best = (value, seed)
    return best[1] if best else None


def run_cell(task):
    """Worker: one search cell (picklable arguments only)."""
    (budget, max_bets, target, objective, stake_mode, families, count,
     min_distance, seconds, reference) = task
    catalogue = catalogue_for(families)
    exclude = ()
    if reference is not None:
        by_key = {(frozenset(b.numbers), b.payout): b for b in catalogue}
        wanted = [(frozenset(numbers), payout) for numbers, payout in reference["keys"]]
        if any(key not in by_key for key in wanted):
            raise ValueError("reference bet is outside the selected catalogue")
        exclude = ([by_key[key] for key in wanted],)
    required = (37 * target + 99) // 100
    result = explore_portfolios(budget, required, max_bets, objective, catalogue, count=count,
                                min_distance=min_distance, stake_mode=stake_mode,
                                time_limit=seconds, exclude=exclude)
    return task, result


def portfolio_row(label, bets, stakes, analysis, extra=None):
    risk = exact_risk(analysis)
    row = {
        "label": label,
        "positions": [{"description": describe_bet(b), "name": b.name,
                       "numbers": list(b.numbers), "payout": b.payout, "chips": int(s)}
                      for b, s in zip(bets, stakes)],
        "profit_by_number": {str(n): str(p) for n, p in enumerate(analysis.profits)},
        "profitable_pockets": analysis.profitable_count,
        "profitable_percentage": float(analysis.profitable_probability * 100),
        "break_even_pockets": analysis.break_even_count,
        "losing_pockets": analysis.loss_count,
        "worst_profit": str(analysis.worst_profit),
        "best_profit": str(analysis.best_profit),
        "total_stake": str(analysis.total_stake),
        "expected_profit": str(analysis.expected_profit),
        "return_per_chip": str(analysis.return_per_unit_staked),
        "expected_shortfall_5pct": str(risk.expected_shortfall),
        "distribution": {str(k): str(v) for k, v in analysis.distribution.items()},
    }
    row.update(extra or {})
    return row


def cell_row(task, result: Exploration, reference_bets, reference_stakes):
    budget, max_bets, target, objective, stake_mode = task[:5]
    rows, offset = [], 0
    if reference_bets:
        rows.append(portfolio_row("A", reference_bets, reference_stakes,
                                  analyse(reference_bets, reference_stakes),
                                  {"source": "existing exact-checked evidence"}))
        offset = 1
    for p in result.portfolios:
        label = chr(ord("A") + offset + p.rank - 1)
        rows.append(portfolio_row(label, p.bets, p.stakes, p.analysis, {
            "source": "explorer", "rank": p.rank, "solver_status": p.solver_status,
            "proven_best_of_remaining": p.proven_best_remaining,
            "objective_value_minimised": str(p.objective_value)}))
    return {
        "chip_budget": budget, "max_bets": max_bets, "target_percentage": target,
        "required_profitable_count": (37 * target + 99) // 100, "objective": objective,
        "objective_text": OBJECTIVE_TEXT[objective], "stake_mode": stake_mode,
        "requested": result.requested, "returned": len(result.portfolios),
        "stop_reason": result.stop_reason, "min_distance": result.min_distance,
        "realised_min_distance": result.realised_min_distance,
        "elapsed_seconds": result.elapsed_seconds, "portfolios": rows,
    }


def markdown(report) -> str:
    out = ["# Roulette Combination Explorer results", "",
           "Fair single-zero European wheel; every portfolio has expected profit "
           "-stake/37 (return -1/37 per chip). Worst loss is the most negative "
           "net profit over the 37 pockets; tail is expected shortfall of loss at "
           "the worst 5% probability mass. Profit is net chips for a single spin.", ""]
    for cell in report["cells"]:
        out += [f"## {cell['chip_budget']} chips, ≤{cell['max_bets']} positions, "
                f"target ≥{cell['target_percentage']}% "
                f"({cell['required_profitable_count']}/37), {cell['objective_text']}, "
                f"stakes: {cell['stake_mode']}", "",
                f"Returned {cell['returned']}/{cell['requested']} "
                f"(stop: {cell['stop_reason']}; realised min bet-set distance "
                f"{cell['realised_min_distance']}).", "",
                "| Combination | Positions (chips) | Profitable pockets | Worst loss | "
                "5% tail loss | Stake | Solver |",
                "|---|---|---|---|---|---|---|"]
        for p in cell["portfolios"]:
            positions = "; ".join(f"{x['description']} ×{x['chips']}" for x in p["positions"])
            tail = Fraction(p["expected_shortfall_5pct"])
            out.append(
                f"| {p['label']}: {p['source']} | {positions} | {p['profitable_pockets']}/37 "
                f"| {p['worst_profit']} | {float(tail):.2f} | {p['total_stake']} "
                f"| {p.get('solver_status', 'recorded')} |")
        out.append("")
        for p in cell["portfolios"]:
            pnl = " ".join(f"{n}:{v}" for n, v in p["profit_by_number"].items())
            out.append(f"- **{p['label']}** net by pocket: {pnl}")
        out.append("")
    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chip-budgets", nargs="+", type=_chip_budget, default=[20])
    parser.add_argument("--max-bets", nargs="+", type=_position_limit, default=[10])
    parser.add_argument("--targets", nargs="+", type=_percentage, default=[70, 80, 90])
    parser.add_argument("--objectives", nargs="+", choices=OBJECTIVES, default=list(OBJECTIVES))
    parser.add_argument("--stakes", nargs="+", choices=("any", "equal"), default=["any"],
                        help="'equal' forces identical chips on every occupied position")
    parser.add_argument("--families", nargs="+", default=list(DEFAULT_FAMILIES),
                        choices=(*european_catalogue(), "all"))
    parser.add_argument("--count", type=_count, default=10, help="portfolios per cell (<=20)")
    parser.add_argument("--min-distance", type=int, default=4,
                        help="minimum symmetric difference between occupied bet sets")
    parser.add_argument("--seconds", type=_seconds, default=30.0, help="solver seconds per MILP")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--references", nargs="*", type=Path,
                        default=[ROOT / "results" / n for n in DEFAULT_REFERENCES])
    parser.add_argument("--allow-large-grid", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    for path in (args.output, args.markdown):
        if path is not None and path.exists():
            raise FileExistsError(f"Preserve existing evidence: {path}")
    if not 1 <= args.min_distance <= 20 or args.jobs < 1:
        parser.error("min-distance must be 1..20 and jobs positive")
    families = list(european_catalogue()) if "all" in args.families \
        else list(dict.fromkeys(args.families))
    catalogue = catalogue_for(families)
    grid = list(product(dict.fromkeys(args.chip_budgets), dict.fromkeys(args.max_bets),
                        dict.fromkeys(args.targets), dict.fromkeys(args.objectives),
                        dict.fromkeys(args.stakes)))
    if len(grid) > 60 and not args.allow_large_grid:
        parser.error(f"{len(grid)} cells requested; pass --allow-large-grid to proceed")
    tasks, references = [], {}
    for budget, max_bets, target, objective, stake_mode in grid:
        required = (37 * target + 99) // 100
        ref = load_references(args.references, catalogue, budget, max_bets, required,
                              objective, stake_mode)
        references[(budget, max_bets, target, objective, stake_mode)] = ref
        tasks.append((budget, max_bets, target, objective, stake_mode, families, args.count,
                      args.min_distance, args.seconds,
                      {"keys": [(sorted(b.numbers), b.payout) for b in ref.bets]} if ref else None))
    cells = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for task, result in pool.map(run_cell, tasks):
            ref = references[task[:5]]
            cells.append(cell_row(task, result, ref.bets if ref else None,
                                  ref.stakes if ref else None))
            print(f"{task[0]}c/{task[1]}p/{task[2]}%/{task[3]}/{task[4]}: "
                  f"{len(result.portfolios)}/{result.requested} ({result.stop_reason})",
                  flush=True)
    run_metadata = metadata()
    run_metadata["rng"] = None
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                              capture_output=True)
    run_metadata["git_revision"] = revision.stdout.strip() if revision.returncode == 0 else None
    status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, text=True,
                            capture_output=True)
    run_metadata["git_dirty"] = bool(status.stdout.strip()) if status.returncode == 0 else None
    try:
        run_metadata["highspy_or_scipy_milp"] = f"scipy {version('scipy')}"
    except PackageNotFoundError:
        pass
    register = ROOT / "docs" / "COMBINATION_EXPLORER_REGISTER.md"
    run_metadata["registration_sha256"] = hashlib.sha256(register.read_bytes()).hexdigest()
    report = {
        "experiment": "C4-001", "wheel": "european", "pockets": 37,
        "families": families, "catalogue_size": len(catalogue),
        "configuration": {
            "chip_budgets": list(dict.fromkeys(args.chip_budgets)),
            "max_bets": list(dict.fromkeys(args.max_bets)),
            "targets_percent": list(dict.fromkeys(args.targets)),
            "objectives": list(dict.fromkeys(args.objectives)),
            "stake_modes": list(dict.fromkeys(args.stakes)),
            "count_per_cell": args.count, "min_bet_set_distance": args.min_distance,
            "seconds_per_milp": args.seconds, "jobs": args.jobs},
        "method": ("Sequential MILP with Hamming-distance cuts on occupied bet sets; "
                   "portfolios repeating an accepted sorted 37-pocket P&L multiset "
                   "are discarded. All portfolios exactly re-settled; no Monte Carlo."),
        "limitations": (
            "One-spin, fair European wheel, integer chips, no table limits or denomination "
            "rules. Solver status 'optimal' is numerical HiGHS evidence, 'limit' means "
            "best found within the time limit. Lists are best-found distinct "
            "alternatives, not an exhaustive enumeration, and a time-limited cell may miss "
            "better portfolios. Every portfolio has expectation exactly -stake/37; "
            "a higher winning frequency is not an edge."),
        "metadata": run_metadata, "cells": cells,
    }
    with args.output.open("x") as handle:
        handle.write(json.dumps(_json_exact(report), indent=2, allow_nan=False) + "\n")
    if args.markdown:
        with args.markdown.open("x") as handle:
            handle.write(markdown(report))
    print(f"Evidence: {args.output}")


if __name__ == "__main__":
    main()
