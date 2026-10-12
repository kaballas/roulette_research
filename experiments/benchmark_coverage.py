"""Registered staged coverage benchmark with exact-checked incumbent reuse."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
from importlib.metadata import PackageNotFoundError, version
from importlib.util import find_spec
import json
from pathlib import Path
import time
import subprocess

from baseline import ROOT, metadata
from optimise_coverage import _chip_budget, _json_exact, _percentage, _position_limit
from roulette.coverage import analyse, european_catalogue
from roulette.coverage_optimisation import optimise_coverage
from roulette.rules import Bet


@dataclass(frozen=True)
class Seed:
    bets: tuple[Bet, ...]
    stakes: tuple[int, ...]
    source: str


def checked_seed(bets, stakes, source, catalogue, budget, max_bets):
    """Accept only exact integer allocations in the selected physical catalogue."""
    bets, stakes = tuple(bets), tuple(stakes)
    legal = {(frozenset(b.numbers), b.payout) for b in catalogue}
    keys = [(frozenset(b.numbers), b.payout) for b in bets]
    if not bets or len(bets) != len(stakes) or len(bets) > max_bets:
        return None
    if len(set(keys)) != len(keys) or not set(keys).issubset(legal):
        return None
    if any(type(stake) is not int or stake <= 0 for stake in stakes):
        return None
    if sum(stakes) != budget:
        return None
    analysis = analyse(bets, stakes)
    if analysis.expected_profit != -analysis.total_stake / 37:
        raise ValueError("Incumbent violates the exact European expectation identity")
    return Seed(bets, stakes, source)


def initial_seeds(catalogue, budget, max_bets, evidence_paths):
    """Load documented allocations and a constructive disjoint-six-line witness."""
    seeds, sources = [], {}
    if budget % 5 == 0:
        six_lines = []
        for start in (1, 7, 13, 19, 25):
            match = next(
                (
                    b
                    for b in catalogue
                    if set(b.numbers) == set(range(start, start + 6))
                ),
                None,
            )
            if match is not None:
                six_lines.append(match)
        seed = checked_seed(
            six_lines,
            [budget // 5] * 5,
            "constructive: five disjoint six-lines",
            catalogue,
            budget,
            max_bets,
        )
        if seed is not None:
            seeds.append(seed)
    for path in evidence_paths:
        content = path.read_bytes()
        sources[str(path.resolve())] = hashlib.sha256(content).hexdigest()
        for index, row in enumerate(json.loads(content)["results"]):
            bets = [
                Bet(b["name"], tuple(b["numbers"]), b["payout"])
                for b in row.get("bets", [])
            ]
            seed = checked_seed(
                bets,
                row.get("stakes", []),
                f"{path.resolve()} results[{index}]",
                catalogue,
                budget,
                max_bets,
            )
            if seed is not None:
                seeds.append(seed)
    return seeds, sources


def best_seed(seeds, required):
    eligible = [
        seed
        for seed in seeds
        if analyse(seed.bets, seed.stakes).profitable_count >= required
    ]
    return max(
        eligible,
        key=lambda seed: analyse(seed.bets, seed.stakes).worst_profit,
        default=None,
    )


def backend_available(backend):
    return backend == "highs" or find_spec("ortools") is not None


def run_stage(backend, mode, seed, catalogue, budget, required, max_bets, seconds):
    started = time.perf_counter()
    try:
        if not backend_available(backend):
            raise ImportError(
                "OR-Tools CP-SAT is not installed; backend not benchmarked"
            )
        result = optimise_coverage(
            budget=budget,
            target_profitable=required,
            max_bets=max_bets,
            time_limit=seconds,
            catalogue=catalogue,
            mode=mode,
            backend=backend,
            incumbent=(seed.bets, seed.stakes) if seed else None,
        )
    except ImportError as exc:
        return {
            "status": "unavailable",
            "backend": backend,
            "mode": mode,
            "reason": str(exc),
            "elapsed_seconds": time.perf_counter() - started,
            "incumbent_source": seed.source if seed else None,
        }, None
    row = _json_exact(asdict(result))
    row["elapsed_seconds"] = time.perf_counter() - started
    row["incumbent_source"] = seed.source if seed else None
    verified = checked_seed(
        result.bets,
        result.stakes,
        f"{backend}/{mode}/target-{required}",
        catalogue,
        budget,
        max_bets,
    )
    if result.analysis is not None:
        if verified is None:
            raise ValueError("Solver returned an invalid incumbent")
        exact = analyse(verified.bets, verified.stakes)
        if exact != result.analysis or exact.profitable_count < required:
            raise ValueError("Solver incumbent failed independent exact settlement")
    return row, verified


def main():
    catalogue = european_catalogue()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chip-budget", type=_chip_budget, default=20)
    parser.add_argument("--max-bets", type=_position_limit, default=10)
    parser.add_argument(
        "--targets", nargs="+", type=_percentage, default=[70, 75, 80, 85, 90]
    )
    parser.add_argument("--seconds", type=int, choices=(60, 300, 900), default=60)
    parser.add_argument(
        "--backends", nargs="+", choices=("highs", "cpsat"), default=["highs", "cpsat"]
    )
    parser.add_argument(
        "--families", nargs="+", choices=(*catalogue, "all"), default=["all"]
    )
    parser.add_argument(
        "--incumbent-evidence",
        nargs="*",
        type=Path,
        default=[ROOT / "results" / "coverage-optimisation-20chips.json"],
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Preserve existing evidence: {args.output}")
    families = (
        list(catalogue)
        if "all" in args.families
        else list(dict.fromkeys(args.families))
    )
    bets = tuple(bet for family in families for bet in catalogue[family])
    seeds, source_hashes = initial_seeds(
        bets, args.chip_budget, args.max_bets, args.incumbent_evidence
    )
    rows = []
    targets = list(dict.fromkeys(args.targets))
    backends = list(dict.fromkeys(args.backends))
    for target in targets:
        required = (37 * target + 99) // 100
        shared_seed = best_seed(seeds, required)
        newly_found = []
        for backend in backends:
            feasibility, feasible_seed = run_stage(
                backend,
                "feasibility",
                shared_seed,
                bets,
                args.chip_budget,
                required,
                args.max_bets,
                args.seconds,
            )
            objective_seed = best_seed(
                [s for s in (shared_seed, feasible_seed) if s is not None], required
            )
            optimisation, optimum_seed = run_stage(
                backend,
                "optimise",
                objective_seed,
                bets,
                args.chip_budget,
                required,
                args.max_bets,
                args.seconds,
            )
            newly_found.extend(
                seed for seed in (feasible_seed, optimum_seed) if seed is not None
            )
            rows.append(
                {
                    "target_percentage": target,
                    "required_profitable_count": required,
                    "backend": backend,
                    "feasibility": feasibility,
                    "optimisation": optimisation,
                }
            )
            print(
                f"{backend} {target}%: feasibility={feasibility['status']}, "
                f"optimisation={optimisation['status']}",
                flush=True,
            )
        seeds.extend(newly_found)
    run_metadata = metadata()
    run_metadata["rng"] = None
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True
    )
    run_metadata["git_revision"] = (
        revision.stdout.strip() if revision.returncode == 0 else None
    )
    try:
        run_metadata["ortools"] = version("ortools")
    except PackageNotFoundError:
        run_metadata["ortools"] = None
    register = ROOT / "docs" / "COVERAGE_SOLVER_REGISTER.md"
    run_metadata["registration_sha256"] = hashlib.sha256(
        register.read_bytes()
    ).hexdigest()
    report = {
        "experiment": f"C3-{args.seconds:03d}",
        "metadata": run_metadata,
        "configuration": {
            "chip_budget": args.chip_budget,
            "max_bets": args.max_bets,
            "targets_percent": targets,
            "seconds_per_stage": args.seconds,
            "backends": backends,
            "families": families,
            "catalogue_size": len(bets),
        },
        "incumbent_evidence_sha256": source_hashes,
        "seed_policy": (
            "Exact-checked recorded and constructive allocations; same initial seed "
            "for both backends at each target. Each backend reuses its feasibility "
            "incumbent for worst-loss optimisation. Completed target allocations "
            "are available to later targets; target order is recorded."
        ),
        "method": "Separate feasibility and worst-loss stages; no Monte Carlo.",
        "limitations": (
            "Fixed integer budget and selected legal catalogue only. Numerical "
            "solver evidence is distinguished from exact mathematical certificates "
            "by optimality_evidence. Feasibility is not worst-loss optimality. "
            "Unavailable backends and unresolved time limits remain explicit."
        ),
        "results": rows,
    }
    with args.output.open("x") as handle:
        handle.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"Evidence: {args.output}")


if __name__ == "__main__":
    main()
