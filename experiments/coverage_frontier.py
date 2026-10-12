"""Exactly re-settle saved candidates and report their unweighted Pareto frontier."""

import argparse
from dataclasses import asdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from baseline import metadata
from optimise_coverage import _json_exact
from roulette.coverage import analyse, european_catalogue
from roulette.coverage_risk import candidate_frontier, exact_risk


def load_candidates(paths):
    """Validate physical positions and independently reconstruct scalar profits."""
    legal = {
        (frozenset(bet.numbers), bet.payout): bet
        for family in european_catalogue().values()
        for bet in family
    }
    candidates = {}
    allocations = {}

    def visit(value, label):
        if isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, f"{label}/{index}")
        elif isinstance(value, dict):
            if value.get("analysis") is not None and "bets" in value and "stakes" in value:
                stakes = tuple(value["stakes"])
                if not stakes or any(type(s) is not int or s <= 0 for s in stakes):
                    raise ValueError("saved stakes must be positive integer chips")
                bets = tuple(
                    legal[(frozenset(b["numbers"]), b["payout"])]
                    for b in value["bets"]
                )
                if len(bets) != len(stakes) or len(bets) > 10 or len(set(bets)) != len(bets):
                    raise ValueError("invalid saved portfolio positions")
                profits = tuple(
                    sum((b.payout + 1) * s for b, s in zip(bets, stakes) if n in b.numbers)
                    - sum(stakes)
                    for n in range(37)
                )
                saved = value["analysis"]
                if profits != tuple(Fraction(p) for p in saved["profits"]):
                    raise ValueError("saved pocket profits fail independent settlement")
                if Fraction(sum(profits), 37) != Fraction(saved["expected_profit"]):
                    raise ValueError("saved expectation fails independent settlement")
                if sum(profits) != -sum(stakes):
                    raise ValueError("standard fair-wheel expected value failed")
                candidates[label] = analyse(bets, stakes)
                allocations[label] = {"bets": [asdict(b) for b in bets], "stakes": stakes}
                return
            for key, item in value.items():
                visit(item, f"{label}/{key}")

    for path in paths:
        visit(json.loads(path.read_text()), str(path))
    if not candidates:
        raise ValueError("no saved feasible portfolios found")
    return candidates, allocations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", nargs="+", type=Path, required=True)
    parser.add_argument("--alpha", default="1/20")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Preserve existing evidence: {args.output}")
    candidates, allocations = load_candidates(args.inputs)
    frontier = candidate_frontier(candidates, args.alpha)
    run_metadata = metadata()
    run_metadata["rng"] = None
    report = {
        "scope": "Nondominated supplied candidates only; global Pareto optimality not established.",
        "axes": ["maximise profitable_count", "maximise worst_profit", "minimise expected_shortfall"],
        "alpha": str(Fraction(args.alpha)),
        "inputs_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in args.inputs},
        "metadata": run_metadata,
        "frontier": frontier,
        "candidates": {
            name: {"allocation": allocations[name], "metrics": asdict(exact_risk(a, args.alpha))}
            for name, a in candidates.items()
        },
    }
    with args.output.open("x") as handle:
        handle.write(json.dumps(_json_exact(report), indent=2, allow_nan=False) + "\n")
    print(f"Retained {len(frontier)} of {len(candidates)} supplied candidates: {args.output}")


if __name__ == "__main__":
    main()
