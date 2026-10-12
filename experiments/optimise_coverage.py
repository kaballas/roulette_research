"""Optimise integer-chip European portfolios for profit frequency and worst loss."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import time

from baseline import ROOT, metadata
from roulette.coverage import european_catalogue
from roulette.coverage_optimisation import optimise_coverage


def _positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _chip_budget(value: str) -> int:
    number = _positive_int(value)
    if number > 1_000_000:
        raise argparse.ArgumentTypeError("chip budget must be between 1 and 1,000,000")
    return number


def _position_limit(value: str) -> int:
    number = _positive_int(value)
    if number > 10:
        raise argparse.ArgumentTypeError("max bets must be between 1 and 10")
    return number


def _percentage(value: str) -> int:
    number = _positive_int(value)
    if number > 100:
        raise argparse.ArgumentTypeError("target percentage must be between 1 and 100")
    return number


def _time_limit(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or not 0 < number <= 3600:
        raise argparse.ArgumentTypeError("time limit must be finite, positive and no greater than 3600 seconds")
    return number


def _json_exact(value):
    """Preserve exact symbolic numbers as fractions, including distribution keys."""
    if isinstance(value, dict):
        return {str(key): _json_exact(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_exact(item) for item in value]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return str(value)


def main() -> None:
    catalogue = european_catalogue()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chip-budget", type=_chip_budget, default=20)
    parser.add_argument("--max-bets", type=_position_limit, default=10)
    parser.add_argument("--targets", nargs="+", type=_percentage, default=[70, 75, 80, 85, 90],
                        help="Minimum strictly profitable percentage; rounded up to whole pockets")
    parser.add_argument("--time-limit", type=_time_limit, default=10.0,
                        help="Solver seconds per target (default: 10)")
    parser.add_argument("--families", nargs="+", choices=(*catalogue, "all"), default=["all"])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Preserve existing evidence: {args.output}")
    families = list(catalogue) if "all" in args.families else list(dict.fromkeys(args.families))
    bets = tuple(bet for family in families for bet in catalogue[family])
    rows = []
    for target in dict.fromkeys(args.targets):
        required = (37 * target + 99) // 100
        started = time.perf_counter()
        result = optimise_coverage(budget=args.chip_budget, target_profitable=required,
                                   max_bets=args.max_bets, time_limit=args.time_limit, catalogue=bets)
        row = _json_exact(asdict(result))
        row.update({"target_percentage": target, "required_profitable_count": required,
                    "elapsed_seconds": time.perf_counter() - started})
        rows.append(row)
        print(f"Target {target}% ({required}/37 pockets): {result.status}", flush=True)
    run_metadata = metadata()
    run_metadata["rng"] = None
    register = ROOT / "docs" / "COVERAGE_OPTIMISATION_REGISTER.md"
    run_metadata["registration_sha256"] = hashlib.sha256(register.read_bytes()).hexdigest()
    report = {"experiment": "C2-001", "wheel": "european", "pockets": 37,
              "families": families, "catalogue_size": len(bets),
              "configuration": {"chip_budget": args.chip_budget, "max_bets": args.max_bets,
                                "targets_percent": list(dict.fromkeys(args.targets)),
                                "time_limit_seconds_per_target": args.time_limit},
              "scope": "Fixed total budget of integer chips on selected legal catalogue bets; at most max_bets occupied positions.",
              "objective": "Maximise the worst-pocket net profit subject to the minimum strictly profitable pocket count.",
              "method": "Mixed integer optimisation; returned portfolios settled exactly on all 37 equally likely pockets. No Monte Carlo confidence interval.",
              "status_interpretation": "Read optimality_evidence with status: analytical_bound_attained and analytical_infeasibility provide exact mathematical certificates within the declared model; numerical_integer_bound and numerical_infeasibility rely on solver bounds and tolerances. Returned allocations are independently checked by exact settlement. Limit may contain a feasible incumbent without established optimality. No proof-assistant verification is claimed.",
              "solver_bound_convention": "Objective and dual bound minimise negative worst-pocket net profit.",
              "metadata": run_metadata, "results": rows}
    with args.output.open("x") as handle:
        handle.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"Evidence: {args.output}")


if __name__ == "__main__":
    main()
