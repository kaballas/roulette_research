"""Exhaustive bounded equal-chip European portfolio coverage search."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from baseline import ROOT, metadata
from roulette.coverage import european_catalogue
from roulette.coverage_search import SearchLimitExceeded, search_coverage


def main() -> None:
    catalogue = european_catalogue()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--families", nargs="+", choices=(*catalogue, "all"), default=["six_line"])
    parser.add_argument("--max-bets", type=int, default=10)
    parser.add_argument("--max-combinations", type=int, default=1_000_000)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "coverage.json")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Preserve existing evidence: {args.output}")
    families = list(catalogue) if "all" in args.families else list(dict.fromkeys(args.families))
    bets = tuple(bet for family in families for bet in catalogue[family])
    try:
        result = search_coverage(bets, args.max_bets, args.max_combinations)
    except SearchLimitExceeded as exc:
        result = {"status": "not_searched", "reason": str(exc), "catalogue_size": len(bets),
                  "max_bets": args.max_bets, "max_combinations": args.max_combinations,
                  "combinations_required": exc.combinations_required, "combinations_searched": 0,
                  "scope": "Distinct selected catalogue bets, exactly one chip each; no unequal stakes or repeated bets."}
    run_metadata = metadata()
    run_metadata["rng"] = None
    result.update({"experiment": "C1-001", "families": families, "metadata": run_metadata})
    with args.output.open("x") as handle:
        handle.write(json.dumps(result, indent=2) + "\n")
    print(f"{result['status']}: {result['combinations_searched']} / "
          f"{result['combinations_required']} combinations; evidence: {args.output}")
    if result["status"] == "not_searched":
        raise SystemExit(result["reason"])


if __name__ == "__main__":
    main()
